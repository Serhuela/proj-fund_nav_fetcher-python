"""Verifica code/services/data_service.py con PostgreSQL simulado en dos bloques.

Resolver asociaciones: traducción en bloque y rechazo de referencias ausentes.
Importar ficheros: rechazo de estructuras inválidas antes de acceder a datos.
La carga válida y su reversión se verifican en integración. Quedan fuera la
lectura de ficheros, el SQL real, las reglas de los repositorios y los logs.
"""

from unittest.mock import Mock

import pytest

from database.postgres import Postgres
from services.data_service import DataService


@pytest.fixture
def service():
    """Construye el servicio con una conexión simulada.

    Returns:
        Servicio y conexión simulada, sin resultados de consultas preparados.
    """
    postgres = Mock(spec=Postgres)
    return DataService(postgres, schema="test_schema"), postgres


# --- Resolver asociaciones. ---


def test_associations_use_two_bulk_lookups_and_preserve_row_order(service):
    """Resuelve referencias repetidas con dos consultas y conserva las filas.

    Args:
        service: Servicio y conexión simulada.
    """
    data, postgres = service
    postgres.fetch_all.side_effect = [
        [{"isin": "ES0123456789", "id": 18}, {"isin": "ES0152769032", "id": 17}],
        [{"code": "other", "id": 24}, {"code": "quefondos", "id": 23}],
    ]
    records = [
        {"fund_isin": "ES0152769032", "source_code": "quefondos", "priority": 1},
        {"fund_isin": "ES0123456789", "source_code": "quefondos", "priority": 2},
        {"fund_isin": "ES0152769032", "source_code": "other", "priority": 3},
        {"fund_isin": "ES0152769032", "source_code": "quefondos", "priority": 1},
    ]
    original_records = [dict(record) for record in records]

    resolved = data._resolve_fund_sources(records)

    assert resolved == [
        {"fund_id": 17, "source_id": 23, "priority": 1},
        {"fund_id": 18, "source_id": 23, "priority": 2},
        {"fund_id": 17, "source_id": 24, "priority": 3},
        {"fund_id": 17, "source_id": 23, "priority": 1},
    ]
    assert records == original_records
    assert postgres.fetch_all.call_count == 2
    fund_lookup, source_lookup = postgres.fetch_all.call_args_list
    fund_references = fund_lookup.args[1][0]
    source_references = source_lookup.args[1][0]
    assert len(fund_references) == 2
    assert set(fund_references) == {"ES0152769032", "ES0123456789"}
    assert len(source_references) == 2
    assert set(source_references) == {"quefondos", "other"}
    postgres.execute.assert_not_called()
    postgres.commit.assert_not_called()
    postgres.rollback.assert_not_called()


@pytest.mark.parametrize("missing_reference", ["fund", "source"])
def test_resolution_rejects_missing_reference(service, missing_reference):
    """Rechaza las asociaciones si falta el fondo o proveedor de una fila.

    Args:
        service: Servicio y conexión simulada.
        missing_reference: Catálogo que omite la referencia de la segunda fila.
    """
    data, postgres = service
    funds = [{"isin": "ES0152769032", "id": 17}]
    sources = [{"code": "quefondos", "id": 23}]
    if missing_reference != "fund":
        funds.append({"isin": "ES0123456789", "id": 18})
    if missing_reference != "source":
        sources.append({"code": "other", "id": 24})
    postgres.fetch_all.side_effect = [funds, sources]

    with pytest.raises(ValueError):
        data._resolve_fund_sources([
            {"fund_isin": "ES0152769032", "source_code": "quefondos"},
            {"fund_isin": "ES0123456789", "source_code": "other"},
        ])

    assert postgres.fetch_all.call_count == 2
    postgres.rollback.assert_not_called()
    postgres.commit.assert_not_called()


# --- Importar ficheros: 1. Rechazar una carga con estructura inválida. ---


@pytest.mark.parametrize(("table", "columns", "rows"), [
    # La tabla no está entre los destinos admitidos por el servicio.
    ("unknown", ["isin"], [("ES0152769032",)]),
    # La cabecera declara dos columnas, pero la fila solo contiene un valor.
    ("funds", ["isin", "name"], [("ES0152769032",)]),
    # Mezcla ISIN e ID de proveedor; debe usar ambas referencias externas o ambos IDs.
    ("fund_sources", ["fund_isin", "source_id"], [("ES0152769032", 23)]),
])
def test_rejects_invalid_import_before_accessing_data(service, table, columns, rows):
    """Rechaza una carga inválida antes de consultar o escribir.

    Args:
        service: Servicio y conexión simulada.
        table: Destino solicitado.
        columns: Cabecera de la carga.
        rows: Valores de la carga.
    """
    data, postgres = service
    with pytest.raises(ValueError):
        data.import_catalog(table, columns, rows)
    assert postgres.mock_calls == []
