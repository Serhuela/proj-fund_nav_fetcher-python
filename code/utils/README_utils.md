# Utilidades

Utilidades compartidas para la configuración y los mensajes de log de la aplicación.

## `custom_logging.py`

Importa `get_logger` y pásale `__name__` para obtener el logger de tu módulo.
Los mensajes se envían a stdout con nivel DEBUG si `APP_ENV` es `development`
(valor por defecto), e INFO en los demás casos.

```python
from utils.custom_logging import get_logger

logger = get_logger(__name__)
logger.info("Aplicación iniciada")
```

## `configuration.py`

Crea una instancia de `Configuration` y lee los parámetros con `get()`, usando
puntos para acceder a claves anidadas. Por defecto carga el `config.yaml` de esta
carpeta; puedes indicar otra ruta al crear la instancia o mediante `APP_CONFIG_FILE`.
Las variables de entorno tienen prioridad sobre el YAML: `DATABASE__SCHEMA`
sobrescribe `database.schema`.

```python
from utils.configuration import Configuration

config = Configuration()
schema = config.get("database.schema", required=True)
interval = config.get("collection.interval_seconds", cast=int)
```
