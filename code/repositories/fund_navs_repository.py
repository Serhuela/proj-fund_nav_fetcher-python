"""Repositorio de los valores liquidativos y su SQL de referencia."""

from pathlib import Path

from repositories.repository import Repository


class FundNavsRepository(Repository):
    """Declara fund_navs y hereda las operaciones comunes sin confirmar cambios."""

    TABLE_NAME = "fund_navs"
    SQL_FILE = Path(__file__).resolve().parents[2] / "data_model" / "04_fund_navs.sql"
    IMPORT_KEYS = ("fund_id", "nav_date")
    IMPORT_COLUMNS = frozenset({
        "fund_id", "nav_date", "nav_value", "fund_source_id", "fetched_at",
    })
