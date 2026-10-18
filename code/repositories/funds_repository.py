"""Inserción de fondos y conversión de sus filas al modelo Fund."""

from collections.abc import Iterable
from pathlib import Path

from psycopg import errors, sql

from database.postgres import Postgres
from models.fund import Fund
from repositories.repository import Repository
from utils.custom_logging import get_logger


logger = get_logger(__name__)


class DuplicateFundError(ValueError):
    """El ISIN ya pertenece a un fondo persistido."""


class FundsRepository(Repository):
    """Conoce la tabla funds; deja la transacción en manos de DataService."""

    TABLE_NAME = "funds"
    SQL_FILE = Path(__file__).resolve().parents[2] / "data_model" / "01_funds.sql"
    IMPORT_KEYS = ("isin",)
    IMPORT_COLUMNS = frozenset({"isin", "name", "currency", "active"})

    def __init__(self, postgres: Postgres, *, schema: str) -> None:
        """Delega en la base usando la tabla y el script declarados por este hijo.

        Args:
            postgres: Conexión compartida, sin transferir su ciclo de vida.
            schema: Nombre literal del esquema que contiene funds.

        Raises:
            ValueError: Si el esquema o los metadatos declarados son inválidos.
        """
        super().__init__(postgres, schema=schema)

    def create(self, isin: str, name: str, currency: str) -> Fund:
        """Inserta un fondo activo y devuelve su ID y valores persistidos.

        Raises:
            DuplicateFundError: Si se repite el ISIN.
            RuntimeError: Si INSERT RETURNING no devuelve la fila esperada.
            psycopg.Error: Ante otras restricciones o errores de persistencia.
        """
        query = sql.SQL(
            "INSERT INTO {} (isin, name, currency) VALUES (%s, %s, %s) "
            "RETURNING id, isin, name, currency, active"
        ).format(self._table)
        logger.debug("Insertando fondo; la confirmación corresponde al servicio.")
        try:
            row = self._postgres.execute(query, (isin, name, currency))
        except errors.UniqueViolation as error:
            if error.diag.constraint_name != "funds_isin_key":
                raise
            raise DuplicateFundError("Ya existe un fondo con ese ISIN.") from None
        if row is None:
            raise RuntimeError("El alta no devolvió el fondo persistido.")
        return Fund(**row)

    def find_id_by_isin(self, isin: str) -> int | None:
        """Busca un fondo reutilizando la consulta en bloque con un único ISIN.

        Args:
            isin: Clave que identifica el fondo en la carga.

        Returns:
            Identificador existente, o None si no se encuentra.

        Raises:
            psycopg.Error: Si falla la consulta.
        """
        fund_ids = self.find_ids_by_isins([isin])
        return fund_ids.get(isin)

    def find_ids_by_isins(self, isins: Iterable[str]) -> dict[str, int]:
        """Busca los identificadores de varios fondos en una sola consulta.

        Args:
            isins: ISIN de los fondos que se quieren resolver.

        Returns:
            Mapa de ISIN a ID, sin las referencias inexistentes. Si la entrada
            está vacía, devuelve un mapa vacío sin consultar PostgreSQL.

        Raises:
            psycopg.Error: Si falla la consulta.
        """
        requested_isins = list(isins)
        if not requested_isins:
            return {}
        query = sql.SQL("SELECT isin, id FROM {} WHERE isin = ANY(%s)").format(self._table)
        rows = self._postgres.fetch_all(query, (requested_isins,))
        return {row["isin"]: row["id"] for row in rows}
