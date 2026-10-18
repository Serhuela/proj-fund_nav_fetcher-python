"""Verifica code/services/data_service.py en PostgreSQL real en dos bloques.

Resolver asociaciones: IDs correctos al combinar varios fondos y proveedores.
Importar ficheros: carga confirmada de los CSV y reversión ante datos inválidos;
el rechazo de estructuras inválidas se verifica en unitarios. Usa tablas
temporales. Quedan fuera permisos, logs y reglas propias de los repositorios.
"""

from pathlib import Path

import pytest
from psycopg import errors

from app.database_cli import _read_csv
from services.data_service import CatalogImportResult, DataService


pytestmark = pytest.mark.integration


# --- Resolver asociaciones. ---


def test_bulk_resolution_with_multiple_funds_and_sources(postgres_with_tables_in_temporary_schema):
    """Guarda cada asociación con los IDs del fondo y proveedor correspondientes.

    Args:
        postgres_with_tables_in_temporary_schema: Conexión con las cuatro tablas temporales vacías.
    """
    service = DataService(postgres_with_tables_in_temporary_schema, schema="pg_temp")
    service.import_catalog(
        "funds", ["isin", "name", "currency"],
        [("ES0152769032", "Primero", "EUR"), ("ES0123456789", "Segundo", "EUR")],
    )
    service.import_catalog(
        "data_sources", ["code", "name", "base_url"],
        [("quefondos", "Principal", "https://example.org"),
         ("other", "Alternativo", "https://other.example.org")],
    )

    result = service.import_catalog(
        "fund_sources", ["fund_isin", "source_code", "priority"],
        [
            ("ES0152769032", "quefondos", 1),
            ("ES0123456789", "quefondos", 2),
            ("ES0152769032", "other", 3),
        ],
    )

    assert result == CatalogImportResult(inserted=3, skipped=0)
    assert postgres_with_tables_in_temporary_schema.fetch_all(
        "SELECT f.isin, ds.code, fs.priority FROM pg_temp.fund_sources AS fs "
        "JOIN pg_temp.funds AS f ON f.id = fs.fund_id "
        "JOIN pg_temp.data_sources AS ds ON ds.id = fs.source_id "
        "ORDER BY fs.priority"
    ) == [
        {"isin": "ES0152769032", "code": "quefondos", "priority": 1},
        {"isin": "ES0123456789", "code": "quefondos", "priority": 2},
        {"isin": "ES0152769032", "code": "other", "priority": 3},
    ]


# --- Importar ficheros: 2. Confirmar una carga válida y devolver sus recuentos. ---


def test_import_mvp_csv_files_and_repeat_without_changes(postgres_with_tables_in_temporary_schema):
    """Carga los CSV, confirma sus datos y comunica las inserciones y omisiones.

    Args:
        postgres_with_tables_in_temporary_schema: Conexión con las cuatro tablas temporales vacías.
    """
    service = DataService(postgres_with_tables_in_temporary_schema, schema="pg_temp")
    catalog = Path(__file__).resolve().parents[3] / "rsc" / "first_mvp"
    tables = ("funds", "data_sources", "fund_sources")
    for table in tables:
        columns, rows = _read_csv(catalog / f"{table}.csv")
        result = service.import_catalog(table, columns, rows)
        assert result == CatalogImportResult(inserted=1, skipped=0)
    # El commit de la importación debe conservar los datos tras otro rollback.
    postgres_with_tables_in_temporary_schema.rollback()
    assert postgres_with_tables_in_temporary_schema.fetch_all(
        "SELECT f.isin, d.code, fs.priority, fs.active, fs.nav_url "
        "FROM pg_temp.fund_sources AS fs "
        "JOIN pg_temp.funds AS f ON f.id = fs.fund_id "
        "JOIN pg_temp.data_sources AS d ON d.id = fs.source_id"
    ) == [{
        "isin": "ES0152769032", "code": "quefondos", "priority": 1, "active": True,
        "nav_url": "https://www.quefondos.com/es/fondos/ficha/index.html?isin=ES0152769032",
    }]
    for table in tables:
        columns, rows = _read_csv(catalog / f"{table}.csv")
        assert service.import_catalog(table, columns, rows) == CatalogImportResult(0, 1)


# --- Importar ficheros: 3. Revertir una carga fallida sin dejar filas parciales. ---


def test_failed_import_leaves_no_partial_rows(postgres_with_tables_in_temporary_schema):
    """La carga falla completa si una fila incumple una restricción.

    Args:
        postgres_with_tables_in_temporary_schema: Conexión con las cuatro tablas temporales vacías.
    """
    service = DataService(postgres_with_tables_in_temporary_schema, schema="pg_temp")
    with pytest.raises(errors.CheckViolation):
        service.import_catalog(
            "funds", ["isin", "name", "currency"],
            [("ES0152769032", "Válido", "EUR"), ("ES0123456789", "Inválido", "eur")],
        )
    assert postgres_with_tables_in_temporary_schema.execute(
        "SELECT count(*) AS total FROM pg_temp.funds"
    ) == {"total": 0}
