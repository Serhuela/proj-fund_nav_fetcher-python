"""Verifica code/services/schema_admin_service.py con PostgreSQL simulado.

Cubre peticiones inválidas sin acceso a datos y reversión ante fallos de ejecución
o confirmación. No comprueba fallos de la propia reversión, SQL, logs, construcción
o delegación interna a repositorios ni resultados reales en PostgreSQL; el ciclo
funcional se verifica en integración.
"""

from unittest.mock import Mock

import pytest

from database.postgres import Postgres
from services.schema_admin_service import SchemaAdminService


ADMIN_OPERATIONS = (
    pytest.param("create_table", ("funds",), id="crear"),
    pytest.param("create_all_tables", (), id="crear-todas"),
    pytest.param("truncate_tables", (["fund_navs"],), id="truncar-una"),
    pytest.param("truncate_tables", (["funds", "fund_navs"],), id="truncar-varias"),
    pytest.param("clear_tables_and_views", (), id="destruir"),
)


@pytest.fixture
def service():
    """Construye el servicio con una conexión simulada y sin abrir PostgreSQL.

    Returns:
        Servicio y conexión simulada, cuyo catálogo contiene una tabla de prueba.
    """
    postgres = Mock(spec=Postgres)
    postgres.fetch_all.return_value = [{"relkind": "r", "relname": "sample_table"}]
    return SchemaAdminService(postgres, schema="test_schema"), postgres


def test_unknown_table_never_touches_database(service):
    """Rechaza la creación de una tabla desconocida sin acceder a PostgreSQL.

    Args:
        service: Servicio y conexión simulada.
    """
    admin, postgres = service
    with pytest.raises(ValueError):
        admin.create_table("unknown")
    assert postgres.mock_calls == []


@pytest.mark.parametrize("tables", [[], ["unknown"], ["funds", "unknown"]])
def test_invalid_truncate_never_touches_database(service, tables):
    """Rechaza el vaciado vacío o con tablas desconocidas sin acceder a datos.

    Args:
        service: Servicio y conexión simulada.
        tables: Selección vacía o con al menos una tabla no admitida.
    """
    admin, postgres = service
    with pytest.raises(ValueError):
        admin.truncate_tables(tables)
    assert postgres.mock_calls == []


@pytest.mark.parametrize(("method_name", "arguments"), ADMIN_OPERATIONS)
@pytest.mark.parametrize("failure_stage", ["execution", "commit"])
def test_operation_failure_rolls_back(service, method_name, arguments, failure_stage):
    """Intenta revertir y propaga el error si falla la ejecución o confirmación.

    Args:
        service: Servicio y conexión simulada.
        method_name: Operación pública que se somete al fallo.
        arguments: Argumentos válidos para la operación.
        failure_stage: Ejecución o confirmación que debe fallar.
    """
    admin, postgres = service
    error = RuntimeError("Fallo simulado de PostgreSQL.")
    failing_method = postgres.execute_script if failure_stage == "execution" else postgres.commit
    failing_method.side_effect = error

    with pytest.raises(RuntimeError) as caught:
        getattr(admin, method_name)(*arguments)

    assert caught.value is error
    postgres.rollback.assert_called_once_with()
    if failure_stage == "execution":
        postgres.commit.assert_not_called()


def test_catalog_failure_rolls_back(service):
    """Intenta revertir también si falla la consulta previa a la limpieza.

    Args:
        service: Servicio y conexión simulada.
    """
    admin, postgres = service
    error = RuntimeError("No se puede consultar el catálogo.")
    postgres.fetch_all.side_effect = error

    with pytest.raises(RuntimeError) as caught:
        admin.clear_tables_and_views()

    assert caught.value is error
    postgres.rollback.assert_called_once_with()
    postgres.commit.assert_not_called()
