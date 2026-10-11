"""Configura los logs en stdout según APP_ENV al importar el módulo.

En development, valor por defecto fuera del contenedor, usa el nivel DEBUG.
En production y en cualquier otro valor usa INFO. La configuración sustituye
los handlers previos del logger raíz.
"""

import logging
import sys
import os

logging.basicConfig(
    level=logging.DEBUG if os.getenv("APP_ENV", "development") == "development" else logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d - %(funcName)s()] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)],  # Dirige los logs a stdout
    # Esto eliminará cualquier handler preexistente en el logger raíz y aplicará esta config.
    force=True
)

# Configurar niveles de logging específicos para librerías externas
# Esto depende de las librerías que estés utilizando en tu proyecto.
# Si ves que te salen muchos logs de ciertas librerías, puedes ajustar sus niveles aquí.
# logging.getLogger("botocore").setLevel(logging.WARNING)
# logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Devuelve el logger identificado por name con la configuración compartida."""
    return logging.getLogger(name)
