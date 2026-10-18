"""Verifica las funcionalidades de code/repositories/repository.py en PostgreSQL.

Cubre existencia, creación, truncado con reinicio de identidad, borrado y sus
dependencias, importación aditiva y errores de datos. Invoca los métodos comunes
heredados por FundsRepository sobre tablas temporales de la conexión. Comprueba
resultados observables; no compara SQL generado, llamadas internas ni logs.
No verifica permisos de despliegue ni modifica tablas permanentes.
"""

import pytest
from psycopg import errors

from repositories.funds_repository import FundsRepository


pytestmark = pytest.mark.integration


@pytest.fixture
def repository(postgres_with_tables_in_temporary_schema):
    """Selecciona la tabla funds del esquema temporal preparado por la conexión.

    Args:
        postgres_with_tables_in_temporary_schema: Conexión con las cuatro tablas temporales vacías.

    Returns:
        Repositorio que usa el nombre real del esquema temporal de esta conexión.
    """
    # pg_temp es un alias; el catálogo guarda un nombre propio para cada conexión.
    schema = postgres_with_tables_in_temporary_schema.execute(
        "SELECT nspname FROM pg_catalog.pg_namespace WHERE oid = pg_my_temp_schema()"
    )
    return FundsRepository(postgres_with_tables_in_temporary_schema, schema=schema["nspname"])


# --- 1. Consultar existencia: distinguir una tabla existente de una ausente. ---


def test_reports_whether_table_exists(repository, postgres_with_tables_in_temporary_schema):
    """Informa de la existencia real y detecta la desaparición de la tabla.

    Args:
        repository: Repositorio sobre funds temporal.
        postgres_with_tables_in_temporary_schema: Conexión con las cuatro tablas temporales vacías.
    """
    assert repository.table_exists() is True
    postgres_with_tables_in_temporary_schema.execute("DROP TABLE pg_temp.funds CASCADE")
    assert repository.table_exists() is False


# --- 2. Crear tablas: disponer de la estructura definida por su script. ---


def test_creates_table_with_usable_structure(empty_postgres):
    """Crea funds desde su SQL y permite guardar los campos y valores por defecto.

    Args:
        empty_postgres: Conexión aislada sin tablas de prueba preparadas.
    """
    repository = FundsRepository(empty_postgres, schema="pg_temp")
    repository.create_table()
    created = empty_postgres.execute(
        "INSERT INTO pg_temp.funds (isin, name, currency) VALUES (%s, %s, %s) "
        "RETURNING isin, name, currency, active",
        ("ES0152769032", "Example", "EUR"),
    )
    assert created == {
        "isin": "ES0152769032", "name": "Example", "currency": "EUR", "active": True,
    }


# --- 3. Vaciar tablas: conservar la estructura y reiniciar los identificadores. ---


def test_truncate_empties_table_and_restarts_identity(empty_postgres):
    """Vacía una tabla poblada y permite insertar de nuevo desde el primer ID.

    Args:
        empty_postgres: Conexión aislada sin tablas de prueba preparadas.
    """
    repository = FundsRepository(empty_postgres, schema="pg_temp")
    repository.create_table()
    empty_postgres.execute(
        "INSERT INTO pg_temp.funds (isin, name, currency) "
        "VALUES (%s, %s, %s), (%s, %s, %s)",
        ("ES0152769032", "First", "EUR", "ES0123456789", "Second", "EUR"),
    )
    repository.truncate_table()
    assert empty_postgres.execute("SELECT count(*) AS total FROM pg_temp.funds") == {"total": 0}
    assert empty_postgres.execute(
        "INSERT INTO pg_temp.funds (isin, name, currency) VALUES (%s, %s, %s) RETURNING id",
        ("ES0152769032", "New", "EUR"),
    ) == {"id": 1}


# --- 4. Eliminar tablas: borrar la estructura y respetar sus dependencias. ---


def test_drop_removes_table(empty_postgres):
    """La tabla desaparece del catálogo al eliminarla.

    Args:
        empty_postgres: Conexión aislada sin tablas de prueba preparadas.
    """
    repository = FundsRepository(empty_postgres, schema="pg_temp")
    repository.create_table()
    repository.drop_table()
    assert empty_postgres.execute("SELECT to_regclass('pg_temp.funds') AS table_name") == {
        "table_name": None,
    }


def test_drop_preserves_table_when_dependents_exist(repository, postgres_with_tables_in_temporary_schema):
    """Una vista dependiente impide el borrado por defecto y conserva ambos objetos.

    Args:
        repository: Repositorio sobre funds temporal.
        postgres_with_tables_in_temporary_schema: Conexión con las cuatro tablas temporales vacías.
    """
    postgres_with_tables_in_temporary_schema.execute(
        "CREATE TEMP VIEW funds_view AS SELECT isin FROM pg_temp.funds"
    )
    postgres_with_tables_in_temporary_schema.commit()
    with pytest.raises(errors.DependentObjectsStillExist):
        repository.drop_table()
    postgres_with_tables_in_temporary_schema.rollback()
    assert postgres_with_tables_in_temporary_schema.execute(
        "SELECT count(*) AS total FROM pg_temp.funds"
    ) == {"total": 0}
    assert postgres_with_tables_in_temporary_schema.execute(
        "SELECT count(*) AS total FROM pg_temp.funds_view"
    ) == {"total": 0}


def test_explicit_cascade_removes_table_and_dependents(empty_postgres):
    """Elimina también la vista dependiente cuando se solicita CASCADE.

    Args:
        empty_postgres: Conexión aislada sin tablas de prueba preparadas.
    """
    repository = FundsRepository(empty_postgres, schema="pg_temp")
    repository.create_table()
    empty_postgres.execute("CREATE TEMP VIEW funds_view AS SELECT isin FROM pg_temp.funds")
    repository.drop_table(cascade=True)
    assert empty_postgres.execute(
        "SELECT to_regclass('pg_temp.funds') AS table_name, "
        "to_regclass('pg_temp.funds_view') AS view_name"
    ) == {"table_name": None, "view_name": None}


# --- 5. Importar registros: añadir nuevos, conservar existentes y contar omisiones. ---


def test_import_adds_new_rows_and_preserves_existing_ones(
    repository, postgres_with_tables_in_temporary_schema,
):
    """Conserva los datos existentes y guarda correctamente mapas con distinto orden.

    Args:
        repository: Repositorio sobre funds temporal.
        postgres_with_tables_in_temporary_schema: Conexión con las cuatro tablas temporales vacías.
    """
    postgres_with_tables_in_temporary_schema.execute(
        "INSERT INTO pg_temp.funds (isin, name, currency) VALUES (%s, %s, %s)",
        ("ES0152769032", "Original", "EUR"),
    )
    original = {"isin": "ES0152769032", "name": "Distinto", "currency": "USD", "active": False}
    new = {"currency": "EUR", "active": False, "name": "O'Brien,\nExample", "isin": "ES0123456789"}
    assert repository.import_records(iter([original, new, new])) == (1, 2)
    assert postgres_with_tables_in_temporary_schema.fetch_all(
        "SELECT isin, name, currency, active FROM pg_temp.funds ORDER BY isin"
    ) == [
        {"isin": "ES0123456789", "name": "O'Brien,\nExample", "currency": "EUR", "active": False},
        {"isin": "ES0152769032", "name": "Original", "currency": "EUR", "active": True},
    ]
    # El repositorio deja la confirmación al servicio: el llamador puede deshacer la carga.
    postgres_with_tables_in_temporary_schema.rollback()
    assert postgres_with_tables_in_temporary_schema.execute(
        "SELECT count(*) AS total FROM pg_temp.funds"
    ) == {"total": 0}


def test_empty_import_keeps_existing_data(repository, postgres_with_tables_in_temporary_schema):
    """Una carga vacía devuelve cero inserciones y omisiones sin borrar datos.

    Args:
        repository: Repositorio sobre funds temporal.
        postgres_with_tables_in_temporary_schema: Conexión con las cuatro tablas temporales vacías.
    """
    postgres_with_tables_in_temporary_schema.execute(
        "INSERT INTO pg_temp.funds (isin, name, currency) VALUES (%s, %s, %s)",
        ("ES0152769032", "Original", "EUR"),
    )
    assert repository.import_records(iter(())) == (0, 0)
    assert postgres_with_tables_in_temporary_schema.execute(
        "SELECT name FROM pg_temp.funds"
    ) == {"name": "Original"}


# --- 6. Comunicar errores de datos: una fila inválida hace fallar la carga. ---


def test_invalid_data_raises_error_without_partial_import(
    repository, postgres_with_tables_in_temporary_schema,
):
    """Propaga el rechazo de PostgreSQL y permite revertir la operación fallida.

    Args:
        repository: Repositorio sobre funds temporal.
        postgres_with_tables_in_temporary_schema: Conexión con las cuatro tablas temporales vacías.
    """
    with pytest.raises(errors.CheckViolation):
        repository.import_records([
            {"isin": "ES0152769032", "name": "Valid", "currency": "EUR"},
            {"isin": "ES0123456789", "name": "Invalid", "currency": "eur"},
        ])
    postgres_with_tables_in_temporary_schema.rollback()
    assert postgres_with_tables_in_temporary_schema.execute(
        "SELECT count(*) AS total FROM pg_temp.funds"
    ) == {"total": 0}
