"""Verifica code/repositories/funds_repository.py contra PostgreSQL real.

Cubre ID generado, valores por defecto, duplicados y ausencia de commit propio.
No verifica reglas del servicio ni tablas permanentes.
"""

import pytest

from repositories.funds_repository import DuplicateFundError, FundsRepository


pytestmark = pytest.mark.integration


# --- Dar de alta: devolver el fondo guardado y dejar la confirmación al llamador. ---


def test_create_returns_generated_fund_without_committing(postgres_with_tables_in_temporary_schema):
    """Devuelve lo persistido, pero permite deshacer la inserción completa.

    Args:
        postgres_with_tables_in_temporary_schema: Conexión con las cuatro tablas temporales vacías.
    """
    repository = FundsRepository(postgres_with_tables_in_temporary_schema, schema="pg_temp")
    fund = repository.create("ES0123456789", "O'Brien", "EUR")
    assert fund.id > 0
    assert (fund.isin, fund.name, fund.currency, fund.active) == (
        "ES0123456789", "O'Brien", "EUR", True,
    )
    postgres_with_tables_in_temporary_schema.rollback()
    assert postgres_with_tables_in_temporary_schema.execute(
        "SELECT count(*) AS total FROM pg_temp.funds"
    ) == {"total": 0}


# --- Rechazar duplicados: comunicar que el ISIN ya existe. ---


def test_create_rejects_duplicate_isin(postgres_with_tables_in_temporary_schema):
    """Rechaza el alta de un ISIN existente mediante DuplicateFundError.

    Args:
        postgres_with_tables_in_temporary_schema: Conexión con las cuatro tablas temporales vacías.
    """
    repository = FundsRepository(postgres_with_tables_in_temporary_schema, schema="pg_temp")
    repository.create("ES0123456789", "Example", "EUR")
    with pytest.raises(DuplicateFundError):
        repository.create("ES0123456789", "Other", "EUR")
    postgres_with_tables_in_temporary_schema.rollback()
