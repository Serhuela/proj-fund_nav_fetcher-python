"""Operaciones DDL explícitas para las tablas del proyecto."""

from collections.abc import Iterable

from psycopg import sql

from database.postgres import Postgres
from repositories.data_sources_repository import DataSourcesRepository
from repositories.fund_navs_repository import FundNavsRepository
from repositories.fund_sources_repository import FundSourcesRepository
from repositories.funds_repository import FundsRepository
from utils.custom_logging import get_logger


logger = get_logger(__name__)


class SchemaAdminService:
    """Crea y elimina objetos del esquema con una conexión de permisos DDL.

    La aplicación normal no debe construir este servicio. El punto de entrada
    administrativo recibe su conexión por separado de la conexión DML del bot.
    El llamador cierra la conexión y no debe dejar escrituras pendientes antes
    de invocar una operación, porque cada método confirma o revierte todo.
    """

    def __init__(self, postgres: Postgres, *, schema: str) -> None:
        """Construye los repositorios sobre la misma conexión privilegiada.

        Args:
            postgres: Conexión DDL dedicada cuyo cierre pertenece al llamador.
            schema: Nombre literal del esquema que se administra.

        Raises:
            ValueError: Si el esquema o los metadatos de un repositorio son inválidos.
        """
        self._postgres = postgres
        self._schema = schema
        # Las tablas se registran en el orden que requieren sus claves foráneas.
        repositories = (
            FundsRepository(postgres, schema=schema),
            DataSourcesRepository(postgres, schema=schema),
            FundSourcesRepository(postgres, schema=schema),
            FundNavsRepository(postgres, schema=schema),
        )
        self._repositories = {repository.TABLE_NAME: repository for repository in repositories}

    def create_table(self, table: str) -> None:
        """Delega la creación de una tabla en su repositorio y confirma el resultado.

        Confirma la creación si termina correctamente. Si falla la ejecución o
        la confirmación, intenta revertir antes de propagar el error. El repositorio
        es el único responsable de conocer, leer y validar su script de creación.

        Args:
            table: Nombre de una tabla atendida por los repositorios del servicio.

        Raises:
            ValueError: Si la tabla no está admitida o falta el marcador de esquema.
            OSError: Si no puede leerse el script, incluido FileNotFoundError.
            UnicodeError: Si el script no está codificado en UTF-8.
            psycopg.Error: Si falla el DDL, la confirmación o la reversión.
        """
        if table not in self._repositories:
            logger.warning("Creación rechazada: la tabla solicitada no está admitida.")
            raise ValueError(f"Tabla no admitida: {table}.")
        repository = self._repositories[table]
        operation = f"creación de {self._schema}.{table}"
        logger.info(f"Iniciando la {operation}.")
        try:
            repository.create_table()
            self._postgres.commit()
        except Exception as error:
            self._rollback_after_error(operation, error)
            raise
        logger.info(f"Creación de {self._schema}.{table} confirmada.")

    def create_all_tables(self) -> None:
        """Crea todas las tablas del proyecto en una única transacción.

        Usa los repositorios en orden de dependencias y confirma al terminar.
        Si falla una creación o la confirmación, intenta revertir la operación
        completa. El esquema debe existir y las tablas no deben estar creadas;
        PostgreSQL admite pg_temp para crear tablas temporales de la conexión.

        Raises:
            ValueError: Si falta el marcador de esquema en un script.
            OSError: Si no puede leerse un script, incluido FileNotFoundError.
            UnicodeError: Si un script no está codificado en UTF-8.
            psycopg.Error: Si falla el DDL, la confirmación o la reversión.
        """
        operation = f"creación de todas las tablas de {self._schema}"
        logger.info(f"Iniciando la {operation}.")
        try:
            for repository in self._repositories.values():
                repository.create_table()
            self._postgres.commit()
        except Exception as error:
            self._rollback_after_error(operation, error)
            raise
        logger.info(f"Creación de todas las tablas de {self._schema} confirmada.")

    def truncate_tables(self, tables: Iterable[str]) -> None:
        """Vacía las tablas juntas y confirma el reinicio de sus identidades.

        Delega una tabla en su repositorio; para varias usa una sola sentencia
        TRUNCATE con RESTRICT, sin añadir automáticamente tablas dependientes.
        Si falla la ejecución o el commit, intenta revertir.

        Args:
            tables: Una o más tablas admitidas, incluidas las dependientes que
                deban vaciarse conjuntamente por sus claves foráneas.

        Raises:
            ValueError: Si no se indican tablas o alguna no está admitida.
            psycopg.Error: Si falla el SQL, la confirmación o la reversión.
        """
        tables = tuple(tables)
        if not tables or any(table not in self._repositories for table in tables):
            logger.warning("Vaciado rechazado: indique una o más tablas admitidas.")
            raise ValueError("Indique una o más tablas admitidas.")
        selected_tables = ", ".join(tables)
        operation = f"vaciado de tablas en {self._schema}: {selected_tables}"
        logger.info(f"Iniciando el {operation}, con reinicio de identidades y sin CASCADE.")
        try:
            if len(tables) == 1:
                self._repositories[tables[0]].truncate_table()
            else:
                identifiers = sql.SQL(", ").join(
                    sql.Identifier(self._schema, table) for table in tables
                )
                statement = sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY RESTRICT").format(identifiers)
                self._postgres.execute_script(statement.as_string())
            self._postgres.commit()
        except Exception as error:
            self._rollback_after_error(operation, error)
            raise
        logger.info(f"Vaciado de {self._schema} confirmado para las tablas: {selected_tables}.")

    def clear_tables_and_views(self) -> tuple[int, int]:
        """Elimina vistas ordinarias y tablas del esquema sin usar CASCADE.

        Conserva el esquema, sus permisos y objetos de otros tipos. Si existe
        una dependencia externa, intenta revertir la operación completa.

        Returns:
            Pareja (tablas eliminadas, vistas eliminadas), después del commit.

        Raises:
            psycopg.Error: Si falla el catálogo, el DDL, el commit o el rollback.
        """
        operation = f"eliminación de tablas y vistas de {self._schema}"
        logger.info(f"Iniciando la {operation} sin CASCADE; se conserva el esquema.")
        try:
            objects = self._postgres.fetch_all(
                "SELECT c.relkind, c.relname "
                "FROM pg_catalog.pg_class AS c "
                "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace "
                "WHERE n.nspname = %s AND c.relkind IN ('v', 'r', 'p') "
                "ORDER BY c.relkind, c.relname",
                (self._schema,),
            )
            views = [row["relname"] for row in objects if row["relkind"] == "v"]
            tables = [row["relname"] for row in objects if row["relkind"] in {"r", "p"}]
            logger.debug(
                f"Catálogo de {self._schema}: {len(tables)} tabla(s) y "
                f"{len(views)} vista(s) ordinaria(s) para eliminar."
            )

            if views:
                logger.debug(f"Eliminando {len(views)} vista(s) ordinaria(s) de {self._schema}.")
                identifiers = sql.SQL(", ").join(
                    sql.Identifier(self._schema, name) for name in views
                )
                self._postgres.execute_script(
                    sql.SQL("DROP VIEW {}").format(identifiers).as_string()
                )
            if tables:
                logger.debug(f"Eliminando {len(tables)} tabla(s) de {self._schema}.")
                identifiers = sql.SQL(", ").join(
                    sql.Identifier(self._schema, name) for name in tables
                )
                self._postgres.execute_script(
                    sql.SQL("DROP TABLE {}").format(identifiers).as_string()
                )
            self._postgres.commit()
        except Exception as error:
            self._rollback_after_error(operation, error)
            raise
        logger.info(
            f"Limpieza de {self._schema} confirmada: {len(tables)} tabla(s) y "
            f"{len(views)} vista(s) eliminadas; esquema y permisos conservados."
        )
        return len(tables), len(views)

    def _rollback_after_error(self, operation: str, error: Exception) -> None:
        """Registra el fallo e intenta revertir sin exponer mensajes del controlador.

        Args:
            operation: Descripción de la operación y su destino, sin datos de filas.
            error: Excepción original que el método público volverá a propagar.

        Raises:
            Exception: Si el rollback falla, propaga ese fallo encadenado al
                original y no afirma que se haya recuperado la transacción.
        """
        logger.error(f"Falló la operación de {operation} ({type(error).__name__}); intentando rollback.")
        try:
            self._postgres.rollback()
        except Exception as rollback_error:
            logger.error(
                f"También falló el rollback de {operation} ({type(rollback_error).__name__}); "
                "no se puede asegurar la reversión de la transacción."
            )
            raise rollback_error from error
        logger.info(f"Rollback de {operation} completado; la operación no se confirmó.")
