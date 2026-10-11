"""Carga parámetros YAML y variables de entorno sin registrar sus valores.

Las variables de entorno tienen prioridad sobre el YAML y el valor por defecto.
El YAML se lee al construir Configuration; el entorno se consulta en cada get().
No carga archivos .env ni modifica las variables del proceso.
"""

import os
from pathlib import Path
from typing import Any, Callable

import yaml


class ConfigurationError(ValueError):
    """Indica un YAML inválido, un parámetro obligatorio ausente o un tipo inválido."""


class Configuration:
    """Proporciona acceso a parámetros anidados y variables de entorno.

    Args:
        path: Ruta del YAML. Si se omite, usa APP_CONFIG_FILE o el config.yaml
            incluido junto a este módulo. Las rutas relativas parten del
            directorio de trabajo del proceso.

    Raises:
        OSError: Si no puede leerse el archivo solicitado.
        ConfigurationError: Si el YAML no es válido o su raíz no es un mapa.
    """

    def __init__(self, path: str | Path | None = None) -> None:
        selected_path = path if path is not None else os.environ.get(
            "APP_CONFIG_FILE", Path(__file__).with_name("config.yaml")
        )
        self._source_path = Path(selected_path).resolve()
        try:
            with self._source_path.open(encoding="utf-8") as stream:
                data = yaml.safe_load(stream)
        except yaml.YAMLError:
            # No exponer fragmentos del YAML
            raise ConfigurationError("El fichero de configuración no es YAML válido.") from None
        if data is None:
            data = {}
        if not isinstance(data, dict):
            raise ConfigurationError("La raíz del YAML debe ser un mapa de parámetros.")
        self._data = data

    @property
    def source_path(self) -> Path:
        """Devuelve la ruta absoluta del fichero YAML cargado."""
        return self._source_path

    def get(
        self,
        key: str,
        default: Any = None,
        *,
        env_var: str | None = None,
        cast: Callable[[Any], Any] | None = None,
        required: bool = False,
    ) -> Any:
        """Obtiene un parámetro aplicando entorno > YAML > default.

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
