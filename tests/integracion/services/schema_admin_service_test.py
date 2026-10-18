"""Verifica code/services/schema_admin_service.py contra PostgreSQL real.

Cubre un ciclo de creación, población, truncado conjunto y eliminación de las
cuatro tablas mediante repositorios y scripts reales. Solo usa el esquema temporal
de esta conexión; no verifica vistas, esquemas permanentes ni permisos de despliegue.
"""

from datetime import date
from decimal import Decimal

import pytest

from services.schema_admin_service import SchemaAdminService
from utils.custom_logging import get_logger


logger = get_logger(__name__)
pytestmark = pytest.mark.integration


def test_create_populate_truncate_and_destroy_temporary_tables(empty_postgres):
    """Comprueba el ciclo completo de las cuatro tablas en el esquema temporal.

    Args:
        empty_postgres: Conexión aislada sin tablas de prueba preparadas.
    """
    admin = SchemaAdminService(empty_postgres, schema="pg_temp")
    tables = ("funds", "data_sources", "fund_sources", "fund_navs")

    # Creación: comprobar que los scripts reales crean las cuatro tablas.
    logger.info("Creando las cuatro tablas en el esquema temporal de la conexión.")
    admin.create_all_tables()

    temporary_tables_query = (
        "SELECT relname FROM pg_catalog.pg_class "
        "WHERE relnamespace = pg_my_temp_schema() AND relkind IN ('r', 'p')"
    )
    created = empty_postgres.fetch_all(temporary_tables_query)
    assert {row["relname"] for row in created} == set(tables), (
        "No se han creado las cuatro tablas esperadas."
    )
    logger.info("Creación comprobada: existen las cuatro tablas en el esquema temporal.")

    # El catálogo ya permite obtener el nombre real de pg_temp para la limpieza.
    temporary_schema_query = (
        "SELECT nspname FROM pg_catalog.pg_namespace WHERE oid = pg_my_temp_schema()"
    )
    temporary_schema = empty_postgres.execute(temporary_schema_query)
    assert temporary_schema is not None, "No se ha localizado el esquema temporal de la conexión."
    admin = SchemaAdminService(empty_postgres, schema=temporary_schema["nspname"])

    # Población: insertar una fila por tabla respetando las claves foráneas.
    logger.info("Poblando las cuatro tablas con datos relacionados.")
    fund = empty_postgres.execute(
        "INSERT INTO pg_temp.funds (isin, name, currency) "
        "VALUES (%s, %s, %s) RETURNING id",
        ("ES0123456789", "Example", "EUR"),
    )
    assert fund is not None, "La inserción del fondo no ha devuelto su identificador."
    source = empty_postgres.execute(
        "INSERT INTO pg_temp.data_sources (code, name, base_url) "
        "VALUES (%s, %s, %s) RETURNING id",
        ("example", "Example source", "https://example.com"),
    )
    assert source is not None, "La inserción de la fuente no ha devuelto su identificador."
    fund_source = empty_postgres.execute(
        "INSERT INTO pg_temp.fund_sources (fund_id, source_id) "
        "VALUES (%s, %s) RETURNING id",
        (fund["id"], source["id"]),
    )
    assert fund_source is not None, (
        "La asociación del fondo y la fuente no ha devuelto su identificador."
    )
    empty_postgres.execute(
        "INSERT INTO pg_temp.fund_navs (fund_id, nav_date, nav_value, fund_source_id) "
        "VALUES (%s, %s, %s, %s)",
        (fund["id"], date(2026, 1, 1), Decimal("123.45"), fund_source["id"]),
    )
    row_counts_query = (
        "SELECT (SELECT count(*) FROM pg_temp.funds) AS funds, "
        "(SELECT count(*) FROM pg_temp.data_sources) AS data_sources, "
        "(SELECT count(*) FROM pg_temp.fund_sources) AS fund_sources, "
        "(SELECT count(*) FROM pg_temp.fund_navs) AS fund_navs"
    )
    assert empty_postgres.execute(row_counts_query) == dict.fromkeys(tables, 1), (
        "No hay exactamente una fila en cada tabla."
    )
    empty_postgres.commit()
    logger.info("Población comprobada y confirmada: hay una fila en cada tabla.")

    # Truncado: vaciar conjuntamente las tablas relacionadas y verificar sus recuentos.
    logger.info("Truncando las cuatro tablas conjuntamente.")
    admin.truncate_tables(tables)
    assert empty_postgres.execute(row_counts_query) == dict.fromkeys(tables, 0), (
        "El truncado no ha dejado todas las tablas vacías."
    )
    logger.info("Truncado comprobado: las cuatro tablas están vacías.")

    # Destrucción: eliminar las tablas mediante el servicio y conservar el esquema.
    logger.info("Destruyendo las cuatro tablas mediante SchemaAdminService.")
    assert admin.clear_tables_and_views() == (4, 0), (
        "La limpieza no ha informado de cuatro tablas y cero vistas eliminadas."
    )
    assert empty_postgres.fetch_all(temporary_tables_query) == [], (
        "Quedan tablas en el esquema temporal tras la limpieza."
    )
    assert empty_postgres.execute(temporary_schema_query) == temporary_schema, (
        "La limpieza no ha conservado el esquema temporal."
    )
    logger.info("Destrucción comprobada: no quedan tablas y el esquema temporal se conserva.")
