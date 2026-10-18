"""Verifica búsquedas de code/repositories/data_sources_repository.py.

Cubre consulta única parametrizada, correspondencia de código a ID y entrada
vacía sin acceso a datos. Comprueba que la búsqueda individual devuelve el ID
o None. No verifica PostgreSQL real ni la importación.
"""

from unittest.mock import Mock

import pytest

from database.postgres import Postgres
from repositories.data_sources_repository import DataSourcesRepository


def test_bulk_lookup_returns_ids_with_one_parameterized_query():
    """Relaciona resultados desordenados con sus códigos sin interpolar valores."""
    postgres = Mock(spec=Postgres)
    postgres.fetch_all.return_value = [
        {"code": "other", "id": 24}, {"code": "quefondos", "id": 23},
    ]
    repository = DataSourcesRepository(postgres, schema="test_schema")
    codes = ["quefondos", "other", "unknown'code"]

    assert repository.find_ids_by_codes(iter(codes)) == {"quefondos": 23, "other": 24}

    postgres.fetch_all.assert_called_once()
    query, parameters = postgres.fetch_all.call_args.args
    assert query.as_string() == (
        'SELECT code, id FROM "test_schema"."data_sources" WHERE code = ANY(%s)'
    )
    assert parameters == (codes,)
    postgres.execute.assert_not_called()
    postgres.commit.assert_not_called()
    postgres.rollback.assert_not_called()


def test_empty_bulk_lookup_does_not_access_database():
    """Devuelve un mapa vacío sin consultas ni cambios en la transacción."""
    postgres = Mock(spec=Postgres)
    repository = DataSourcesRepository(postgres, schema="test_schema")

    assert repository.find_ids_by_codes(iter([])) == {}
    assert postgres.mock_calls == []


@pytest.mark.parametrize("source_id", [23, None])
def test_single_lookup_returns_id_or_none(source_id):
    """Conserva el resultado individual con una sola consulta de referencias.

    Args:
        source_id: ID del proveedor encontrado, o None si no existe.
    """
    postgres = Mock(spec=Postgres)
    code = "quefondos"
    postgres.fetch_all.return_value = [] if source_id is None else [{"code": code, "id": source_id}]
    repository = DataSourcesRepository(postgres, schema="test_schema")

    assert repository.find_id_by_code(code) == source_id
    postgres.fetch_all.assert_called_once()
    assert postgres.fetch_all.call_args.args[1] == ([code],)
    postgres.execute.assert_not_called()
    postgres.commit.assert_not_called()
    postgres.rollback.assert_not_called()
