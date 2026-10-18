# Utilidades

Utilidades compartidas para la configuración y los mensajes de log de la aplicación.

## Logs

Importa `get_logger` y pásale `__name__` para obtener el logger de tu módulo.
Los mensajes se envían a stdout con nivel DEBUG si `APP_ENV` es `development`
(valor por defecto), e INFO en los demás casos.

```python
from utils.custom_logging import get_logger

logger = get_logger(__name__)
logger.info("Aplicación iniciada")
```

## Configuración

Los parámetros se resuelven en este orden de prioridad:

1. Variables de entorno.
2. Perfil activo (`development` o `production`) del YAML.
3. Valores comunes de la sección `default` del mismo YAML.

`APP_ENV` selecciona el perfil; por defecto se usa `development` (excepto en producción que ya lo fija el dockerfile en `production`). La configuración
está en `config.yaml`; `APP_CONFIG_FILE` permite indicar otra ruta.

```python
from utils.configuration import Configuration

config = Configuration()
schema = config.get("database.schema", required=True)
interval = config.get("collection.interval_seconds", cast=int)
```
