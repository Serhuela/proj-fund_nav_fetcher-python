"""Verifica las búsquedas de code/repositories/funds_repository.py.

Cubre consulta única parametrizada, correspondencia de ISIN a ID y entrada
vacía sin acceso a datos. Comprueba que la búsqueda individual devuelve el ID
o None. No verifica PostgreSQL real ni el alta de fondos.
"""

from unittest.mock import Mock

import pytest

from database.postgres import Postgres
from repositories.funds_repository import FundsRepository


def test_bulk_lookup_returns_ids_with_one_parameterized_query():
    """Relaciona resultados desordenados con sus ISIN sin interpolar valores."""
    postgres = Mock(spec=Postgres)
    postgres.fetch_all.return_value = [
        {"isin": "ES0123456789", "id": 18}, {"isin": "ES0152769032", "id": 17},
    ]
    repository = FundsRepository(postgres, schema="test_schema")
    isins = ["ES0152769032", "ES0123456789", "unknown'isin"]

    assert repository.find_ids_by_isins(iter(isins)) == {"ES0152769032": 17, "ES0123456789": 18}

    postgres.fetch_all.assert_called_once()
    query, parameters = postgres.fetch_all.call_args.args
    assert query.as_string() == 'SELECT isin, id FROM "test_schema"."funds" WHERE isin = ANY(%s)'
    assert parameters == (isins,)
    postgres.execute.assert_not_called()
    postgres.commit.assert_not_called()
    postgres.rollback.assert_not_called()


def test_empty_bulk_lookup_does_not_access_database():
    """Devuelve un mapa vacío sin consultas ni cambios en la transacción."""
    postgres = Mock(spec=Postgres)
    repository = FundsRepository(postgres, schema="test_schema")

    assert repository.find_ids_by_isins(iter([])) == {}
    assert postgres.mock_calls == []


@pytest.mark.parametrize("fund_id", [17, None])
def test_single_lookup_returns_id_or_none(fund_id):
    """Conserva el resultado individual con una sola consulta de referencias.

    Args:
        fund_id: ID del fondo encontrado, o None si no existe.
    """
    postgres = Mock(spec=Postgres)
    isin = "ES0152769032"
    postgres.fetch_all.return_value = [] if fund_id is None else [{"isin": isin, "id": fund_id}]
    repository = FundsRepository(postgres, schema="test_schema")

    assert repository.find_id_by_isin(isin) == fund_id
    postgres.fetch_all.assert_called_once()
    assert postgres.fetch_all.call_args.args[1] == ([isin],)
    postgres.execute.assert_not_called()
    postgres.commit.assert_not_called()
    postgres.rollback.assert_not_called()
