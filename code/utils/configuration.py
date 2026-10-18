"""Carga parámetros YAML y variables de entorno sin registrar sus valores.

La prioridad es: variables de entorno > perfil activo > perfil default.
APP_ENV selecciona development o production; si falta, se usa development.
"""

import os
from enum import Enum
from pathlib import Path
from typing import Any, Callable

import yaml


class Environment(str, Enum):
    """Entornos de ejecución admitidos por la aplicación."""

    DEVELOPMENT = "development"
    PRODUCTION = "production"


class ConfigurationError(ValueError):
    """Indica un YAML inválido, un perfil inválido o un parámetro incorrecto."""


class Configuration:
    """Proporciona acceso a parámetros anidados de YAML y del entorno.

    Args:
        path: Ruta del YAML. Si se omite, usa APP_CONFIG_FILE o el config.yaml
            incluido junto a este módulo. Las rutas relativas parten del
            directorio de trabajo del proceso.

    Raises:
        OSError: Si no puede leerse el archivo solicitado.
        ConfigurationError: Si la raíz del YAML no es un mapa o APP_ENV no es
            uno de los entornos admitidos.
    """

    def __init__(self, path: str | Path | None = None) -> None:
        """Lee el YAML y combina default con el entorno indicado por APP_ENV."""
        selected_path = path if path is not None else os.environ.get(
            "APP_CONFIG_FILE", Path(__file__).with_name("config.yaml")
        )
        self._source_path = Path(selected_path).resolve()
        try:
            with self._source_path.open(encoding="utf-8") as stream:
                data = yaml.safe_load(stream)
        except yaml.YAMLError:
            # No exponer fragmentos del YAML.
            raise ConfigurationError("El fichero de configuración no es YAML válido.") from None
        if data is None:
            data = {}
        if not isinstance(data, dict):
            raise ConfigurationError("La raíz del YAML debe ser un mapa de parámetros.")

        environment_value = os.environ.get("APP_ENV", Environment.DEVELOPMENT.value)
        try:
            self._environment = Environment(environment_value)
        except ValueError:
            raise ConfigurationError(
                "APP_ENV debe ser development o production."
            ) from None

        self._data = self._merge(
            data.get("default", {}),
            data.get(self._environment.value, {}),
        )

    @classmethod
    def _merge(cls, base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
        """Devuelve una combinación recursiva sin modificar los mapas originales."""
        result = dict(base)
        for key, value in overrides.items():
            if isinstance(result.get(key), dict) and isinstance(value, dict):
                result[key] = cls._merge(result[key], value)
            else:
                result[key] = value
        return result

    @property
    def source_path(self) -> Path:
        """Devuelve la ruta absoluta del fichero YAML cargado."""
        return self._source_path

    @property
    def environment(self) -> Environment:
        """Devuelve el entorno enumerado seleccionado mediante APP_ENV."""
        return self._environment

    def get(
        self,
        key: str,
        default: Any = None,
        *,
        env_var: str | None = None,
        cast: Callable[[Any], Any] | None = None,
        required: bool = False,
    ) -> Any:
        """Obtiene un parámetro aplicando entorno > perfil > default.

        Args:
            key: Ruta separada por puntos, por ejemplo database.schema.
            default: Valor usado si la ruta no existe en el YAML ni en el entorno.
            env_var: Nombre de entorno alternativo. Por defecto se transforma
                database.schema en DATABASE__SCHEMA.
            cast: Conversión opcional, por ejemplo int o float. Para booleanos
                acepta bool con true/false, yes/no, on/off o 1/0.
            required: Rechaza valores ausentes, nulos o cadenas vacías.

        Returns:
            El valor seleccionado, convertido si se solicita. Sin cast, el
            entorno devuelve cadenas y el YAML conserva sus tipos originales.

        Raises:
            ConfigurationError: Si falta un valor obligatorio o falla la
                conversión por ValueError o TypeError. No incluye su valor.
        """
        variable = env_var if env_var is not None else key.upper().replace(".", "__")
        if variable in os.environ:
            value = os.environ[variable]
        else:
            value = self._data
            for part in key.split("."):
                if not isinstance(value, dict) or part not in value:
                    value = default
                    break
                value = value[part]
        if required and (value is None or value == ""):
            raise ConfigurationError(f"Falta el parámetro obligatorio: {key}.")
        if cast is None or value is None:
            return value
        try:
            if cast is bool:
                normalized = str(value).strip().lower()
                if normalized in {"true", "yes", "on", "1"}:
                    return True
                if normalized in {"false", "no", "off", "0"}:
                    return False
                raise ValueError
            return cast(value)
        except (ValueError, TypeError):
            raise ConfigurationError(f"Tipo inválido para el parámetro: {key}.") from None
