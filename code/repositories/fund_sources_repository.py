"""Repositorio de las asociaciones entre fondos y proveedores y su SQL."""

from pathlib import Path

from repositories.repository import Repository


class FundSourcesRepository(Repository):
    """Persiste asociaciones con IDs resueltos por el servicio de importación."""

    TABLE_NAME = "fund_sources"
    SQL_FILE = Path(__file__).resolve().parents[2] / "data_model" / "03_fund_sources.sql"
    IMPORT_KEYS = ("fund_id", "source_id")
    IMPORT_COLUMNS = frozenset({
        "fund_id", "source_id", "external_id", "nav_url", "priority", "active",
    })
