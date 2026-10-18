"""Verifica las entradas de importación de code/repositories/repository.py.

Cubre aceptación de registros válidos con PostgreSQL simulado y rechazo de tipos
incorrectos, columnas inválidas o inconsistentes y claves obligatorias ausentes
antes de acceder a datos. Usa los metadatos de funds para invocar la importación
heredada. Los efectos reales se comprueban en
tests/integracion/repositories/repository_test.py.
"""

from unittest.mock import Mock

import pytest

from database.postgres import Postgres
from repositories.funds_repository import FundsRepository


# --- 5. Aceptar registros válidos y devolver el resultado de la importación. ---


def test_import_accepts_valid_records():
    """Acepta una carga válida sin error y devuelve su recuento de inserciones."""
    postgres = Mock(spec=Postgres)
    postgres.fetch_all.return_value = [{"inserted": 1}]
    repository = FundsRepository(postgres, schema="test_schema")
    records = [{"isin": "ES0152769032", "name": "Example", "currency": "EUR"}]

    assert repository.import_records(records) == (1, 0)


# --- 6. Rechazar entradas inválidas antes de acceder a datos. ---


@pytest.mark.parametrize("records", [None, {"isin": "ES0152769032"}, ["texto"]])
def test_import_rejects_invalid_input_types(records):
    """Rechaza entradas que no representan una colección de registros.

    Args:
        records: Entrada con un tipo incompatible con la importación.
    """
    postgres = Mock(spec=Postgres)
    repository = FundsRepository(postgres, schema="test_schema")
    with pytest.raises(TypeError):
        repository.import_records(records)
    assert postgres.mock_calls == []


@pytest.mark.parametrize("records", [
    [{}],
    [{"id": 1, "isin": "ES0152769032"}],
    [{"name": "Fondo sin clave"}],
    [{"isin": "ES0152769032", "unknown": "dato"}],
    [
        {"isin": "ES0152769032", "name": "Example", "currency": "EUR"},
        {"isin": "ES0123456789"},
    ],
])
def test_import_rejects_malformed_records(records):
    """Rechaza la carga completa si las columnas de algún registro son inválidas.

    Args:
        records: Registros vacíos, con columnas no admitidas, sin clave o inconsistentes.
    """
    postgres = Mock(spec=Postgres)
    repository = FundsRepository(postgres, schema="test_schema")
    with pytest.raises(ValueError):
        repository.import_records(records)
    assert postgres.mock_calls == []
