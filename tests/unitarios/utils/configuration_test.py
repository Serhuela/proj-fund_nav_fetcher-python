"""Verifica code/utils/configuration.py mediante ficheros temporales.

Cubre prioridad de entorno/YAML/default, rutas, conversiones y errores sin
valores sensibles. No cubre despliegue Docker, credenciales reales ni validación
de reglas de negocio del bot.
"""

import pytest

from utils.configuration import Configuration, ConfigurationError


@pytest.fixture
def config_file(tmp_path):
    """Crea un YAML mínimo para comprobar lectura y sobrescritura."""
    path = tmp_path / "config.yaml"
    path.write_text("database:\n  schema: funds\ncollection:\n  interval_seconds: 3600\n", encoding="utf-8")
    return path


def test_yaml_environment_and_default(config_file, monkeypatch):
    """Respeta la prioridad y consulta el entorno en cada lectura."""
    monkeypatch.delenv("DATABASE__SCHEMA", raising=False)
    monkeypatch.delenv("MISSING__KEY", raising=False)
    config = Configuration(config_file)
    assert config.get("database.schema") == "funds"
    assert config.get("missing.key", 42) == 42
    monkeypatch.setenv("DATABASE__SCHEMA", "override")
    assert config.get("database.schema") == "override"


def test_credentials_and_empty_environment(config_file, monkeypatch):
    """Lee los nombres de credenciales existentes y rechaza vacíos obligatorios."""
    config = Configuration(config_file)
    monkeypatch.setenv("BBDD_BOT_PASSWORD", "test-secret")
    assert config.get("database.password", env_var="BBDD_BOT_PASSWORD", required=True) == "test-secret"
    monkeypatch.setenv("DATABASE__SCHEMA", "")
    with pytest.raises(ConfigurationError):
        config.get("database.schema", required=True)


def test_conversion_and_redaction(config_file, monkeypatch):
    """Convierte intervalos y evita divulgar valores en errores de conversión."""
    config = Configuration(config_file)
    monkeypatch.setenv("COLLECTION__INTERVAL_SECONDS", "7200")
    assert config.get("collection.interval_seconds", cast=int) == 7200
    monkeypatch.setenv("COLLECTION__INTERVAL_SECONDS", "secret-value")
    with pytest.raises(ConfigurationError) as error:
        config.get("collection.interval_seconds", cast=int)
    assert "secret-value" not in str(error.value)


@pytest.mark.parametrize("value, expected", [("false", False), ("0", False), ("TRUE", True), ("yes", True)])
def test_boolean_conversion(config_file, monkeypatch, value, expected):
    """Interpreta cadenas booleanas sin usar su mera presencia como verdad."""
    monkeypatch.setenv("ENABLED", value)
    assert Configuration(config_file).get("enabled", cast=bool) is expected


def test_invalid_boolean_conversion_is_redacted(config_file, monkeypatch):
    """Rechaza booleanos no reconocidos sin incluir su valor en el error."""
    invalid_value = "maybe-secret"
    monkeypatch.setenv("ENABLED", invalid_value)

    with pytest.raises(ConfigurationError) as error:
        Configuration(config_file).get("enabled", cast=bool)

    assert "Tipo inválido para el parámetro: enabled." == str(error.value)
    assert invalid_value not in str(error.value)


def test_path_selection(config_file, monkeypatch, tmp_path):
    """Prioriza ruta explícita, luego APP_CONFIG_FILE y después el YAML incluido."""
    monkeypatch.setenv("APP_CONFIG_FILE", str(tmp_path / "absent.yaml"))
    explicit_config = Configuration(config_file)
    assert explicit_config.source_path == config_file.resolve()
    assert explicit_config.get("database.schema", env_var="TEST_SCHEMA") == "funds"
    with pytest.raises(FileNotFoundError):
        Configuration()
    monkeypatch.setenv("APP_CONFIG_FILE", str(config_file))
    environment_config = Configuration()
    assert environment_config.source_path == config_file.resolve()
    assert environment_config.get("database.schema", env_var="TEST_SCHEMA") == "funds"
    monkeypatch.delenv("APP_CONFIG_FILE")
    monkeypatch.chdir(tmp_path)
    assert Configuration().get("database.schema", env_var="TEST_SCHEMA") == "nav"


@pytest.mark.parametrize("contents", ["- list", "42", "password: [secret-value"])
def test_invalid_yaml(tmp_path, contents):
    """Rechaza raíces distintas de mapas y YAML inválido sin mostrar su contenido."""
    path = tmp_path / "invalid.yaml"
    path.write_text(contents, encoding="utf-8")
    with pytest.raises(ConfigurationError) as error:
        Configuration(path)
    assert "secret-value" not in str(error.value)


def test_empty_yaml_and_required_values(tmp_path, monkeypatch):
    """Admite ficheros vacíos y detecta parámetros obligatorios ausentes."""
    monkeypatch.delenv("MISSING", raising=False)
    path = tmp_path / "empty.yaml"
    path.write_text("", encoding="utf-8")
    config = Configuration(path)
    assert config.get("missing", "fallback") == "fallback"
    with pytest.raises(ConfigurationError):
        config.get("missing", required=True)
