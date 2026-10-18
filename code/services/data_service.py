"""Interfaz de acceso a datos para los bots y coordinación de sus transacciones."""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from database.postgres import Postgres
from repositories.data_sources_repository import DataSourcesRepository
from repositories.fund_navs_repository import FundNavsRepository
from repositories.fund_sources_repository import FundSourcesRepository
from repositories.funds_repository import FundsRepository
from utils.custom_logging import get_logger


logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class CatalogImportResult:
    """Resumen de filas añadidas y omitidas por conflictos de unicidad."""

    inserted: int
    skipped: int


class DataService:
    """Centraliza las operaciones de base de datos que necesitan los bots.

    Los bots acceden a los datos a través de este servicio, que coordina los
    repositorios y confirma o revierte la transacción de cada operación.
    El llamador proporciona una conexión dedicada, sin escrituras pendientes,
    y se encarga de cerrarla.
    """

    def __init__(self, postgres: Postgres, *, schema: str) -> None:
        """Prepara los repositorios compartiendo conexión y los organiza por tabla.

        Args:
            postgres: Conexión compartida por los repositorios de esta carga.
            schema: Nombre del esquema de destino.

        Raises:
            ValueError: Si el esquema no es válido.
        """
        self._postgres = postgres

        self._funds = FundsRepository(postgres, schema=schema)
        self._data_sources = DataSourcesRepository(postgres, schema=schema)
        self._fund_sources = FundSourcesRepository(postgres, schema=schema)
        self._fund_navs = FundNavsRepository(postgres, schema=schema)

        self._repositories = {
            self._funds.TABLE_NAME: self._funds,
            self._data_sources.TABLE_NAME: self._data_sources,
            self._fund_sources.TABLE_NAME: self._fund_sources,
            self._fund_navs.TABLE_NAME: self._fund_navs,
        }

    def import_catalog(
        self,
        table: str,
        columns: Sequence[str],
        rows: Iterable[Sequence[Any]],
    ) -> CatalogImportResult:
        """Importa una tabla sin borrar registros ausentes del fichero de origen.

        Recibe la cabecera y filas ya leídas. Las asociaciones admiten las
        referencias fund_isin y source_code juntas, o los IDs de la base.
        Conserva las filas existentes y cuenta como omitida cualquier fila
        que choque con una clave única, incluidos duplicados de la propia carga.

        Args:
            table: Tabla de catálogo atendida por el servicio.
            columns: Cabecera de la carga, sin la columna id autogenerada.
            rows: Filas con los valores en el orden de la cabecera.

        Returns:
            Recuentos de filas insertadas y omitidas por unicidad.

        Raises:
            ValueError: Si la estructura es inválida o falta una referencia.
            psycopg.Error: Si falla la persistencia o la transacción.
        """
        logger.debug(f"Paso 1/5 de importación en {table}: validando tabla y cabecera.")
        if table not in self._repositories:
            raise ValueError(f"Tabla de catálogo no admitida: {table}.")
        repository = self._repositories[table]
        columns = tuple(columns)
        if (
            not columns
            or any(not isinstance(column, str) or not column.strip() for column in columns)
            or len(set(columns)) != len(columns)
        ):
            raise ValueError("La cabecera necesita nombres únicos y no vacíos.")

        allowed_columns = repository.IMPORT_COLUMNS
        key_columns = repository.IMPORT_KEYS
        external_references = table == "fund_sources" and bool(
            {"fund_isin", "source_code"} & set(columns)
        )
        if external_references:
            allowed_columns = (allowed_columns - {"fund_id", "source_id"}) | {
                "fund_isin", "source_code",
            }
            key_columns = ("fund_isin", "source_code")
        if not set(columns) <= allowed_columns or not set(key_columns) <= set(columns):
            raise ValueError("Columnas inválidas: incluya las claves y no incluya id.")

        logger.debug(f"Paso 2/5 de importación en {table}: preparando y validando las filas.")
        records = []
        for row in rows:
            values = tuple(row)
            if len(values) != len(columns):
                raise ValueError("Cada fila debe tener los valores de la cabecera.")
            record = dict(zip(columns, values))
            records.append(record)
        if not records:
            logger.info(f"Importación de {table} finalizada: carga vacía, 0 filas añadidas y 0 omitidas.")
            return CatalogImportResult(inserted=0, skipped=0)

        logger.info(f"Importando {len(records)} registro(s) en {table}.")
        try:
            if external_references:
                logger.debug(f"Paso 3/5 de importación en {table}: resolviendo referencias en bloque.")
                records = self._resolve_fund_sources(records)
            else:
                logger.debug(
                    f"Paso 3/5 de importación en {table}: resolución de referencias no necesaria."
                )
            logger.debug(f"Paso 4/5 de importación en {table}: insertando registros mediante el repositorio.")
            inserted, skipped = repository.import_records(records)
            logger.debug(f"Paso 5/5 de importación en {table}: confirmando la transacción.")
            self._postgres.commit()
        except Exception:
            logger.debug(f"Revirtiendo la transacción de importación en {table} tras un error.")
            self._postgres.rollback()
            raise

        logger.info(
            f"Importación de {table} confirmada: {inserted} fila(s) añadida(s) "
            f"y {skipped} omitida(s)."
        )
        return CatalogImportResult(inserted=inserted, skipped=skipped)

    def _resolve_fund_sources(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Resuelve las referencias únicas en bloque y prepara las asociaciones.

        Ejecuta una consulta para los fondos y otra para los proveedores.
        Conserva el orden y los duplicados de las asociaciones recibidas.

        Args:
            records: Asociaciones con fund_isin y source_code.

        Returns:
            Copias de los registros con fund_id y source_id en lugar de esas claves.

        Raises:
            ValueError: Si un fondo o proveedor no existe.
            psycopg.Error: Si falla una consulta de referencias.
        """
        fund_isins = {record["fund_isin"] for record in records}
        source_codes = {record["source_code"] for record in records}
        fund_ids = self._funds.find_ids_by_isins(fund_isins)
        source_ids = self._data_sources.find_ids_by_codes(source_codes)

        resolved = []
        for record in records:
            prepared = dict(record)
            fund_id = fund_ids.get(prepared.pop("fund_isin"))
            if fund_id is None:
                raise ValueError("El fondo de la asociación no existe; importe funds primero.")
            source_id = source_ids.get(prepared.pop("source_code"))
            if source_id is None:
                raise ValueError("El proveedor de la asociación no existe; importe data_sources primero.")
            prepared["fund_id"] = fund_id
            prepared["source_id"] = source_id
            resolved.append(prepared)
        return resolved
