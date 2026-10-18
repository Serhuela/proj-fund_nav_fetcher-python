"""Verifica code/database/postgres.py contra PostgreSQL real.

Cubre resultados de consultas con parámetros, commit, rollback y reutilización
tras errores con una tabla temporal. No verifica opciones de conexión, COPY,
credenciales de despliegue, concurrencia ni tablas permanentes.
"""

import psycopg
import pytest


pytestmark = pytest.mark.integration


# --- Consultar: devolver una fila o todas las filas y conservar los parámetros. ---


def test_queries_return_rows_and_preserve_parameters(empty_postgres):
    """Devuelve los datos recibidos, incluido texto con comas y apóstrofos.

    Args:
        empty_postgres: Conexión aislada con PostgreSQL de desarrollo.
    """
    query = (
        "SELECT name FROM (VALUES (1, %s), (2, %s)) AS sample(position, name) "
        "ORDER BY position"
    )
    parameters = ("O'Brien, sample", "Segundo")
    assert empty_postgres.execute(query, parameters) == {"name": "O'Brien, sample"}
    assert empty_postgres.fetch_all(query, parameters) == [
        {"name": "O'Brien, sample"}, {"name": "Segundo"},
    ]


# --- Transacciones: confirmar cambios y deshacer los pendientes. ---


def test_commit_and_rollback(postgres_with_tables_in_temporary_schema):
    """El rollback descarta lo pendiente sin perder la escritura confirmada.

    Args:
        postgres_with_tables_in_temporary_schema: Conexión con las cuatro tablas temporales vacías.
    """
    postgres_with_tables_in_temporary_schema.execute(
        "INSERT INTO pg_temp.funds (isin, name, currency) VALUES (%s, %s, %s)",
        ("ES0123456789", "Example", "EUR"),
    )
    postgres_with_tables_in_temporary_schema.commit()
    postgres_with_tables_in_temporary_schema.execute("DELETE FROM pg_temp.funds")
    assert postgres_with_tables_in_temporary_schema.execute(
        "SELECT count(*) AS total FROM pg_temp.funds"
    ) == {"total": 0}
    postgres_with_tables_in_temporary_schema.rollback()
    assert postgres_with_tables_in_temporary_schema.execute(
        "SELECT count(*) AS total FROM pg_temp.funds"
    ) == {"total": 1}


# --- Recuperación: volver a consultar después de un error y su reversión. ---


def test_connection_recovers_after_rollback(empty_postgres):
    """Una transacción abortada vuelve a admitir consultas tras rollback.

    Args:
        empty_postgres: Conexión aislada con PostgreSQL de desarrollo.
    """
    with pytest.raises(psycopg.errors.DivisionByZero):
        empty_postgres.execute("SELECT 1 / 0")
    empty_postgres.rollback()
    assert empty_postgres.execute("SELECT 1 AS value") == {"value": 1}
