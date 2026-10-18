"""Persistencia común por tabla, sin gestionar conexiones ni transacciones."""

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, ClassVar

from psycopg import sql

from database.postgres import Postgres
from utils.custom_logging import get_logger


logger = get_logger(__name__)


class Repository:
    """Comparte conexión, metadatos y operaciones administrativas por tabla.

    La base declara TABLE_NAME y SQL_FILE; cada concreto define sus valores
    como atributos de clase, junto con IMPORT_KEYS e IMPORT_COLUMNS.
    El constructor valida los metadatos antes de usar la conexión.
    El servicio decide cuándo confirmar o revertir y proporciona una conexión con los
    permisos necesarios: heredar métodos DDL no concede privilegios al bot.
    No se invocan otros repositorios ni se almacena la existencia de la tabla.
    """

    # Cada hijo debe definir el nombre de su tabla y la ruta de su script.
    TABLE_NAME: ClassVar[str]
    SQL_FILE: ClassVar[Path]

    # Los concretos declaran las columnas y claves naturales de su catálogo.
    IMPORT_KEYS: ClassVar[tuple[str, ...]] = ()
    IMPORT_COLUMNS: ClassVar[frozenset[str] | None] = None

    def __init__(
        self,
        postgres: Postgres,
        *,
        schema: str,
    ) -> None:
        """Recibe la conexión compartida y los metadatos del repositorio concreto.

        Args:
            postgres: Conexión cuyo ciclo de vida pertenece al llamador.
            schema: Nombre literal del esquema. La tabla y el script SQL son
                declaraciones obligatorias del repositorio concreto.

        Raises:
            ValueError: Si el esquema, el nombre de tabla o la ruta SQL son
                inválidos. No se accede a PostgreSQL durante la construcción.
        """
        if not isinstance(schema, str) or not schema:
            raise ValueError("El esquema debe ser un nombre no vacío.")
        table_name = getattr(self, "TABLE_NAME", None)
        sql_file = getattr(self, "SQL_FILE", None)
        if not isinstance(table_name, str) or not table_name:
            raise ValueError("El repositorio debe declarar un nombre de tabla no vacío.")
        if not isinstance(sql_file, Path):
            raise ValueError("El repositorio debe declarar la ruta SQL como Path.")
        self._postgres = postgres
        self._schema = schema
        self._table = sql.Identifier(schema, self.TABLE_NAME)

    def table_exists(self) -> bool:
        """Consulta si existe la tabla ordinaria o particionada en este momento.

        No considera las vistas como tablas ni garantiza que otro proceso no
        elimine el objeto después de la consulta. Abre una transacción de lectura
        si la conexión todavía no tiene una activa.

        Returns:
            True si el catálogo contiene la tabla en el esquema configurado.

        Raises:
            RuntimeError: Si la consulta no devuelve su resultado booleano.
            psycopg.Error: Si falla la consulta del catálogo.
        """
        logger.debug(
            f"Consultando la existencia de la tabla {self._schema}.{self.TABLE_NAME} "
            "en el catálogo de PostgreSQL."
        )
        row = self._postgres.execute(
            "SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_class AS c "
            "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace "
            "WHERE n.nspname = %s AND c.relname = %s "
            "AND c.relkind IN ('r', 'p')) AS table_exists",
            (self._schema, self.TABLE_NAME),
        )
        if row is None:
            raise RuntimeError("La consulta de existencia no devolvió un resultado.")
        exists = bool(row["table_exists"])
        logger.debug(
            f"Consulta de existencia de {self._schema}.{self.TABLE_NAME} completada: "
            f"{'existe' if exists else 'no existe'}."
        )
        return exists

    def create_table(self) -> None:
        """Ejecuta el script de creación de confianza dentro de la transacción.

        Sustituye el marcador por el esquema citado; no comprueba previamente
        la existencia ni oculta el error si la tabla ya existe. El SQL versionado
        determina los objetos creados y debe corresponder a este repositorio.

        Raises:
            ValueError: Si falta el marcador de esquema en el script.
            OSError: Si no se puede leer el script, incluido FileNotFoundError.
            UnicodeError: Si el script no está codificado en UTF-8.
            psycopg.Error: Si PostgreSQL rechaza el script.
        """
        logger.debug(
            f"Preparando la creación de {self._schema}.{self.TABLE_NAME} "
            f"desde el script {self.SQL_FILE}."
        )
        statement = self.SQL_FILE.read_text(encoding="utf-8")
        if "[SCHEMA_PLACEHOLDER]" not in statement:
            raise ValueError("El script SQL no contiene [SCHEMA_PLACEHOLDER].")
        statement = statement.replace(
            "[SCHEMA_PLACEHOLDER]", sql.Identifier(self._schema).as_string(),
        )
        self._postgres.execute_script(statement)
        logger.info(
            f"Script de creación de {self._schema}.{self.TABLE_NAME} ejecutado; "
            "cambios pendientes de confirmar por el servicio."
        )

    def truncate_table(self) -> None:
        """Vacía la tabla y reinicia sus identidades sin confirmar ni usar CASCADE.

        RESTRICT rechaza dependencias que requieren truncar otras tablas juntas;
        esa operación conjunta corresponde al coordinador, no a un bucle de
        llamadas a este método. Los efectos quedan pendientes de commit.

        Raises:
            psycopg.Error: Si faltan permisos, no existe la tabla o hay dependencias.
        """
        logger.debug(
            f"Ejecutando el vaciado de {self._schema}.{self.TABLE_NAME} "
            "con reinicio de identidades y RESTRICT."
        )
        statement = sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY RESTRICT").format(
            self._table,
        )
        self._postgres.execute_script(statement.as_string())
        logger.info(
            f"Vaciado y reinicio de identidades de {self._schema}.{self.TABLE_NAME} ejecutados; "
            "cambios pendientes de confirmar por el servicio."
        )

    def drop_table(self, cascade: bool = False) -> None:
        """Elimina la tabla y sus datos sin confirmar la transacción.

        No omite el error si no existe. Por defecto, las dependencias externas
        impiden el borrado. Con cascade=True se eliminan también los objetos
        dependientes, incluso si pertenecen a otros esquemas. El servicio debe
        revertir si la operación falla.

        Args:
            cascade: Autoriza eliminar objetos dependientes mediante CASCADE.
                Si es False, utiliza RESTRICT.

        Raises:
            psycopg.Error: Si faltan permisos, no existe la tabla o hay dependencias.
        """
        logger.debug(
            f"Ejecutando la eliminación de {self._schema}.{self.TABLE_NAME} "
            f"con {'CASCADE' if cascade else 'RESTRICT'}."
        )
        behavior = sql.SQL("CASCADE" if cascade else "RESTRICT")
        statement = sql.SQL("DROP TABLE {} {}").format(self._table, behavior)
        self._postgres.execute_script(statement.as_string())
        logger.info(
            f"Eliminación de {self._schema}.{self.TABLE_NAME} ejecutada; "
            "cambios pendientes de confirmar por el servicio."
        )

    def import_records(self, records: Iterable[Mapping[str, Any]]) -> tuple[int, int]:
        """Inserta la carga en bloque y omite filas con conflictos de unicidad.

        Conserva las filas existentes sin comparar ni actualizar sus valores.
        Otros errores de datos o restricciones abortan la sentencia. El servicio
        confirma o revierte la transacción completa.

        Materializa la carga en memoria y la envía en una sola sentencia.
        Está pensado para catálogos pequeños, dentro del límite de parámetros
        de PostgreSQL; no divide automáticamente cargas masivas.

        Args:
            records: Mapas con las mismas columnas, sin id y con valores preparados.

        Returns:
            Pareja (filas insertadas, filas omitidas por conflictos de unicidad).

        Raises:
            TypeError: Si la carga no es un iterable de mapas.
            ValueError: Si las columnas o claves son inválidas.
            psycopg.Error: Si falla la inserción o una restricción distinta de unicidad.

        """
        columns, rows = self._prepare_import_records(records)
        if not rows:
            return 0, 0

        column_sql = sql.SQL(", ").join(sql.Identifier(column) for column in columns)
        placeholders = sql.SQL(", ").join(sql.Placeholder() for _ in columns)
        row_sql = sql.SQL("({})").format(placeholders)
        values_sql = sql.SQL(", ").join(row_sql for _ in rows)
        statement = sql.SQL(
            "INSERT INTO {} ({}) VALUES {} ON CONFLICT DO NOTHING RETURNING 1 AS inserted"
        ).format(self._table, column_sql, values_sql)
        parameters = tuple(value for row in rows for value in row)
        inserted = len(self._postgres.fetch_all(statement, parameters))
        skipped = len(rows) - inserted
        logger.info(
            f"Importación en {self._schema}.{self.TABLE_NAME}: "
            f"{inserted} fila(s) insertada(s) y {skipped} omitida(s); "
            "cambios pendientes de confirmar por el servicio."
        )
        return inserted, skipped

    def _prepare_import_records(
        self, records: Iterable[Mapping[str, Any]],
    ) -> tuple[tuple[str, ...], list[tuple[Any, ...]]]:
        """Valida la estructura y ordena los valores de la carga antes de escribir.

        Args:
            records: Mapas con columnas y valores. Puede ser un generador vacío.

        Returns:
            Columnas del primer registro y filas con sus valores en ese mismo orden.
            Conserva los valores recibidos, incluidos nulos y cadenas vacías.

        Raises:
            TypeError: Si no se recibe un iterable de mapas.
            ValueError: Si faltan claves o las columnas son inválidas o inconsistentes.
        """
        if isinstance(records, Mapping):
            raise TypeError("Indique un iterable de registros, no un único mapa.")
        columns: tuple[str, ...] = ()
        rows = []
        for record in records:
            if not isinstance(record, Mapping):
                raise TypeError("Cada registro debe ser un mapa de columnas y valores.")
            if (
                not record or "id" in record
                or any(not isinstance(column, str) or not column.strip() for column in record)
            ):
                raise ValueError("Cada registro necesita columnas válidas y no puede incluir id.")
            if not columns:
                columns = tuple(record)
                if self.IMPORT_COLUMNS is not None and not set(columns) <= self.IMPORT_COLUMNS:
                    raise ValueError("La carga contiene columnas no admitidas por la tabla.")
                if not set(self.IMPORT_KEYS) <= set(columns):
                    raise ValueError("La carga necesita las claves naturales de la tabla.")
            elif set(record) != set(columns):
                raise ValueError("Todos los registros deben contener las mismas columnas.")
            rows.append(tuple(record[column] for column in columns))
        return columns, rows
