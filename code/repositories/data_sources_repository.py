"""Repositorio de la tabla de proveedores de datos y su SQL de referencia."""

from collections.abc import Iterable
from pathlib import Path

from psycopg import sql

from repositories.repository import Repository


class DataSourcesRepository(Repository):
    """Declara data_sources y hereda las operaciones comunes sin confirmar cambios."""

    TABLE_NAME = "data_sources"
    SQL_FILE = Path(__file__).resolve().parents[2] / "data_model" / "02_data_sources.sql"
    IMPORT_KEYS = ("code",)
    IMPORT_COLUMNS = frozenset({"code", "name", "base_url", "active"})

    def find_id_by_code(self, code: str) -> int | None:
        """Busca un proveedor reutilizando la consulta en bloque con un código.

        Args:
            code: Clave que identifica el proveedor en la carga.

        Returns:
            Identificador existente, o None si no se encuentra.

        Raises:
            psycopg.Error: Si falla la consulta.
        """
        source_ids = self.find_ids_by_codes([code])
        return source_ids.get(code)

    def find_ids_by_codes(self, codes: Iterable[str]) -> dict[str, int]:
        """Busca los identificadores de varios proveedores en una sola consulta.

        Args:
            codes: Códigos de los proveedores que se quieren resolver.

        Returns:
            Mapa de código a ID, sin las referencias inexistentes. Si la entrada
            está vacía, devuelve un mapa vacío sin consultar PostgreSQL.

        Raises:
            psycopg.Error: Si falla la consulta.
        """
        requested_codes = list(codes)
        if not requested_codes:
            return {}
        query = sql.SQL("SELECT code, id FROM {} WHERE code = ANY(%s)").format(self._table)
        rows = self._postgres.fetch_all(query, (requested_codes,))
        return {row["code"]: row["id"] for row in rows}
