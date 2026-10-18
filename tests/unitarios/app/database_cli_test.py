"""Verifica la lectura y las protecciones de code/app/database_cli.py.

Cubre lectura de CSV con BOM, comillas y campos vacíos, rechazo de estructuras
inválidas, confirmación del destino exacto y rechazo de conexiones no permitidas.
No verifica el despacho de main, argparse, ExitStack, logs, SQL ni credenciales
reales. Las operaciones de datos y esquema se prueban en sus servicios.
"""

from unittest.mock import Mock

import pytest

from app import database_cli
from utils.configuration import Environment


# --- Leer CSV: conservar sus valores y rechazar estructuras ambiguas. ---


def test_read_csv_preserves_values_and_empty_fields(tmp_path):
    """Lee BOM y comillas, conserva el texto y convierte campos vacíos en None.

    Args:
        tmp_path: Carpeta temporal para el fichero CSV.
    """
    source = tmp_path / "funds.csv"
    source.write_text(
        '\ufeffisin,name,currency,active\n'
        'ES0152769032,"Fondo, ejemplo",EUR,\n'
        "ES0123456789,O'Brien,USD,true\n",
        encoding="utf-8",
    )

    columns, rows = database_cli._read_csv(source)

    assert columns == ["isin", "name", "currency", "active"]
    assert rows == [
        ("ES0152769032", "Fondo, ejemplo", "EUR", None),
        ("ES0123456789", "O'Brien", "USD", "true"),
    ]


@pytest.mark.parametrize("contents", [
    # Un fichero vacío no tiene cabecera.
    pytest.param("", id="sin-cabecera"),
    # Las columnas repetidas harían que se perdieran valores al leer el CSV.
    pytest.param("name,name\na,b\n", id="columnas-repetidas"),
    # Los identificadores los genera PostgreSQL, no el fichero.
    pytest.param("id,isin\n1,ES0152769032\n", id="id-manual"),
    # La fila contiene menos valores que los declarados en la cabecera.
    pytest.param("isin,name\nES0152769032\n", id="faltan-valores"),
    # La fila contiene más valores que los declarados en la cabecera.
    pytest.param("isin\nES0152769032,Example\n", id="sobran-valores"),
])
def test_read_csv_rejects_invalid_structure(tmp_path, contents):
    """Rechaza ficheros cuya estructura no permite interpretar bien sus datos.

    Args:
        tmp_path: Carpeta temporal para el fichero CSV.
        contents: Contenido que incumple la estructura admitida.
    """
    source = tmp_path / "invalid.csv"
    source.write_text(contents, encoding="utf-8")

    with pytest.raises(ValueError):
        database_cli._read_csv(source)


# --- Confirmar el destino: exigir el nombre completo antes de autorizar borrados. ---


@pytest.mark.parametrize(("answer", "expected"), [
    pytest.param("psql_ddbb_dev_fund_nav.nav", True, id="destino-exacto"),
    pytest.param("psql_ddbb_dev_fund_nav.other", False, id="destino-distinto"),
])
def test_confirmation_requires_exact_target(monkeypatch, answer, expected):
    """Solo autoriza la operación cuando se escribe el destino completo correcto.

    Args:
        monkeypatch: Sustituye la respuesta por teclado.
        answer: Destino que escribe el usuario.
        expected: Indica si la respuesta debe autorizar la operación.
    """
    monkeypatch.setattr("builtins.input", Mock(return_value=answer))

    assert database_cli._confirm("nav", "Eliminar tablas.") is expected


# --- Proteger la conexión: rechazar destinos fuera del desarrollo permitido. ---


@pytest.mark.parametrize(("environment", "database_name", "schema"), [
    pytest.param(
        Environment.PRODUCTION, "psql_ddbb_dev_fund_nav", "nav", id="produccion",
    ),
    pytest.param(
        Environment.DEVELOPMENT, "other_database", "nav", id="otra-base",
    ),
    pytest.param(
        Environment.DEVELOPMENT, "psql_ddbb_dev_fund_nav", "public", id="esquema-protegido",
    ),
])
def test_connection_rejects_forbidden_destination(monkeypatch, environment, database_name, schema):
    """Rechaza destinos prohibidos antes de abrir una conexión PostgreSQL.

    Args:
        monkeypatch: Sustituye la configuración y la apertura de conexiones.
        environment: Entorno solicitado por la configuración.
        database_name: Nombre de la base de datos configurada.
        schema: Esquema de destino solicitado.
    """
    config = Mock(environment=environment)
    config.get.return_value = database_name
    connect = Mock()
    monkeypatch.setattr(database_cli, "Configuration", Mock(return_value=config))
    monkeypatch.setattr(database_cli, "Postgres", connect)

    with pytest.raises(ValueError):
        database_cli._connect("BBDD_DEPLOY", schema)

    connect.assert_not_called()
