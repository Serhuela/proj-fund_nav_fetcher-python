"""Soporte de integración del acceso a datos sobre tablas temporales.

Ofrece una conexión sin tablas de prueba y, opcionalmente, las cuatro tablas
temporales vacías. Usa Configuration y las credenciales BBDD_BOT únicamente
contra desarrollo; no accede a tablas permanentes ni omite errores de conexión.
"""

from collections.abc import Iterator

import pytest

from database.postgres import Postgres
from services.schema_admin_service import SchemaAdminService
from utils.configuration import Configuration, ConfigurationError, Environment


DEVELOPMENT_DATABASE = "psql_ddbb_dev_fund_nav"


@pytest.fixture
def empty_postgres() -> Iterator[Postgres]:
    """Abre una conexión de desarrollo sin crear tablas de prueba.

    Reutiliza los parámetros YAML y sus sobrescrituras de entorno. Rechaza
    producción y cualquier nombre distinto de la base de desarrollo antes de
    conectar. Cierra la conexión al terminar cada test, eliminando los objetos
    temporales que la prueba haya creado.

    Yields:
        Conexión aislada sin tablas de prueba preparadas.

    Raises:
        ConfigurationError: Si el destino o los parámetros no son válidos.
        OSError: Si no se puede leer la configuración.
        UnicodeError: Si la configuración no está codificada en UTF-8.
        psycopg.Error: Si falla la conexión.
    """
    config = Configuration()
    if config.environment != Environment.DEVELOPMENT:
        raise ConfigurationError("Las pruebas de integración solo admiten APP_ENV=development.")
    database_name = config.get("database.name", required=True)
    if database_name != DEVELOPMENT_DATABASE:
        raise ConfigurationError(
            f"Las pruebas de integración solo admiten la base {DEVELOPMENT_DATABASE}."
        )
    database = Postgres(
        host=config.get("database.host", required=True),
        port=config.get("database.port", cast=int, required=True),
        dbname=database_name,
        user=config.get("database.username", env_var="BBDD_BOT_USERNAME", required=True),
        password=config.get("database.password", env_var="BBDD_BOT_PASSWORD", required=True),
        sslmode=config.get("database.sslmode", required=True),
        connect_timeout=config.get("database.connect_timeout", cast=int, required=True),
    )
    try:
        yield database
    finally:
        database.close()


@pytest.fixture
def postgres_with_tables_in_temporary_schema(empty_postgres: Postgres) -> Postgres:
    """Prepara las cuatro tablas vacías en el esquema temporal de la conexión.

    Usa SchemaAdminService sobre pg_temp para crear las tablas en orden de
    dependencias. No inserta datos. Cada test añade los registros que necesita
    y sus rollback conservan las tablas. El rol BBDD_BOT necesita permiso TEMPORARY.

    Args:
        empty_postgres: Conexión aislada proporcionada por la fixture empty_postgres.

    Returns:
        La misma conexión, con funds, data_sources, fund_sources y fund_navs vacías.

    Raises:
        ValueError: Si los metadatos o los scripts de los repositorios son inválidos.
        OSError: Si no se puede leer un script.
        UnicodeError: Si un script no está codificado en UTF-8.
        psycopg.Error: Si falla la creación o su confirmación.
    """
    admin = SchemaAdminService(empty_postgres, schema="pg_temp")
    admin.create_all_tables()
    return empty_postgres
