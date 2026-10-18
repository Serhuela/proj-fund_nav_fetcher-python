"""Comandos manuales de desarrollo que componen los servicios de base de datos."""

import argparse
import csv
from contextlib import ExitStack
from pathlib import Path

from database.postgres import Postgres
from services.data_service import DataService
from services.schema_admin_service import SchemaAdminService
from utils.configuration import Configuration, Environment
from utils.custom_logging import get_logger


logger = get_logger(__name__)

DEVELOPMENT_DATABASE = "psql_ddbb_dev_fund_nav"
TABLES = ("funds", "data_sources", "fund_sources", "fund_navs")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Define los comandos y lee sus argumentos de la línea de comandos.

    Args:
        argv: Argumentos que se quieren interpretar. Si es None, usa los
            recibidos al ejecutar el programa.

    Returns:
        Operación solicitada y argumentos correspondientes al comando.

    Raises:
        SystemExit: Si se solicita la ayuda o los argumentos no son válidos.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)

    create = subparsers.add_parser("create", help="Crear una tabla desde data_model/.")
    create.add_argument("table", choices=TABLES)
    create.add_argument("--schema")

    load = subparsers.add_parser("load", help="Importar filas CSV de forma aditiva.")
    load.add_argument("table", choices=TABLES)
    load.add_argument("csv_file", type=Path)
    load.add_argument("--schema")

    truncate = subparsers.add_parser("truncate", help="Vaciar tablas y reiniciar sus IDs.")
    truncate.add_argument("tables", nargs="+", choices=TABLES)
    truncate.add_argument("--schema")

    clear = subparsers.add_parser("clear", help="Eliminar tablas y vistas ordinarias del esquema.")
    clear.add_argument("--schema")

    return parser.parse_args(argv)


def _connect(prefix: str, schema: str | None) -> tuple[Postgres, str]:
    """Conecta solo a desarrollo usando explícitamente el rol solicitado."""
    config = Configuration()
    if config.environment != Environment.DEVELOPMENT:
        raise ValueError("Estos comandos solo admiten APP_ENV=development.")
    database = config.get("database.name", required=True)
    if database != DEVELOPMENT_DATABASE:
        raise ValueError(f"Estos comandos solo admiten la base {DEVELOPMENT_DATABASE}.")
    selected_schema = schema if schema is not None else config.get("database.schema", required=True)
    if (
        not selected_schema or selected_schema == "public"
        or selected_schema == "information_schema" or selected_schema.startswith("pg_")
    ):
        raise ValueError("No se admite un esquema vacío, public ni esquemas de sistema.")

    postgres = Postgres(
        host=config.get("database.host", required=True),
        port=config.get("database.port", cast=int, required=True),
        dbname=database,
        user=config.get("database.username", env_var=f"{prefix}_USERNAME", required=True),
        password=config.get("database.password", env_var=f"{prefix}_PASSWORD", required=True),
        sslmode=config.get("database.sslmode", required=True),
        connect_timeout=config.get("database.connect_timeout", cast=int, required=True),
        options="-c lock_timeout=5000",
    )
    return postgres, selected_schema


def _confirm(schema: str, action: str) -> bool:
    """Exige escribir el destino completo antes de limpiar objetos o filas."""
    target = f"{DEVELOPMENT_DATABASE}.{schema}"
    logger.info(f"{action} Destino: {target}.")
    if input(f"Escribe {target} para confirmar: ") != target:
        logger.info("Operación cancelada.")
        return False
    return True


def _read_csv(path: Path) -> tuple[list[str], list[tuple[str | None, ...]]]:
    """Lee un CSV UTF-8 y prepara sus valores sin acceder a PostgreSQL.

    Args:
        path: Fichero con cabecera, separador coma y comillas dobles.

    Returns:
        Cabecera y filas en su orden original. Los campos vacíos representan None;
        el resto conserva su texto para que PostgreSQL aplique el tipo del destino.

    Raises:
        ValueError: Si la cabecera o el número de columnas no son válidos.
        OSError: Si no puede leerse el fichero.
        UnicodeError: Si el contenido no es UTF-8.
        csv.Error: Si el lector no puede interpretar el CSV.
    """
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        columns = reader.fieldnames or []
        if not columns or any(not column for column in columns) or len(set(columns)) != len(columns):
            raise ValueError("El CSV necesita una cabecera con nombres únicos y no vacíos.")
        if "id" in columns:
            raise ValueError("No incluya id en el CSV: PostgreSQL lo genera.")
        rows = []
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError("Todas las filas CSV deben tener las columnas de la cabecera.")
            rows.append(tuple(row[column] if row[column] != "" else None for column in columns))
    return columns, rows


def main(argv: list[str] | None = None) -> None:
    """Prepara ambos servicios y ejecuta la operación solicitada.

    Abre una conexión con BBDD_BOT para DataService y otra con BBDD_DEPLOY para
    SchemaAdminService. Requiere ambas credenciales para cualquier operación.
    Cierra las conexiones abiertas incluso si falla la preparación o ejecución.

    Args:
        argv: Argumentos del comando. Si es None, usa los recibidos al ejecutar
            el programa.
    """
    args = parse_args(argv)

    with ExitStack() as connections:
        bot_postgres, schema = _connect("BBDD_BOT", args.schema)
        connections.callback(bot_postgres.close)
        deploy_postgres, _ = _connect("BBDD_DEPLOY", schema)
        connections.callback(deploy_postgres.close)

        data_service = DataService(bot_postgres, schema=schema)
        schema_admin_service = SchemaAdminService(deploy_postgres, schema=schema)

        if args.operation == "load":
            columns, rows = _read_csv(args.csv_file)
            result = data_service.import_catalog(args.table, columns, rows)
            logger.info(f"Añadidas: {result.inserted}; omitidas: {result.skipped}.")
            return

        if args.operation == "create":
            schema_admin_service.create_table(args.table)
            logger.info(f"Tabla creada: {schema}.{args.table}")
            return

        if args.operation == "truncate":
            tables = ", ".join(args.tables)
            action = f"Se vaciarán estas tablas: {tables}"
            if not _confirm(schema, action):
                return
            schema_admin_service.truncate_tables(args.tables)
            logger.info("Tablas vaciadas; estructura conservada.")
            return

        if args.operation == "clear":
            action = (
                "Se eliminarán las tablas y vistas del esquema. "
                "El esquema y sus permisos se conservarán."
            )
            if not _confirm(schema, action):
                return
            tables, views = schema_admin_service.clear_tables_and_views()
            logger.info(f"Eliminadas: {tables} tablas y {views} vistas.")
            return

        raise ValueError(f"Operación no admitida: {args.operation}.")


if __name__ == "__main__":
    main()
