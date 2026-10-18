# Ejecutar la aplicación y las pruebas en desarrollo

Ejecuta los comandos desde la raíz del repositorio, con el
[entorno de desarrollo preparado](entorno_desarrollo.md):

```bash
source .venv/bin/activate
export APP_ENV=development
```

Para las operaciones que acceden a PostgreSQL, carga las credenciales en esa
misma terminal siguiendo la [guía de credenciales](credentials/gestion_credenciales.md#cargar-credenciales).

## Ejecutar la aplicación

```bash
python -m app.main
```

La aplicación usa `APP_ENV=development` automáticamente si la variable no está
definida en la sesión.

## Ejecutar las pruebas

Para ejecutar las pruebas unitarias:

```bash
python -m pytest
```

Para ejecutar todas las pruebas, incluidas las de integración:

```bash
python -m pytest -m ""
```

Para ejecutar solo las de integración:

```bash
python -m pytest -m integration
```

La opción `-m ""` anula el filtro `not integration` de `pyproject.toml`.
La configuración ejecuta las pruebas en paralelo, muestra la cobertura en la
terminal y genera el informe HTML en `htmlcov/index.html`.

Las pruebas de integración requieren PostgreSQL de desarrollo accesible y las
credenciales DML cargadas. El rol necesita permiso `TEMPORARY`; las pruebas
trabajan con tablas temporales y no requieren crear las tablas de la aplicación.
Los requisitos y las variantes de ejecución se detallan en la
[documentación de pruebas](../../tests/README_tests.md).

Al terminar, [retira las credenciales de la terminal y bloquea Bitwarden](credentials/gestion_credenciales.md#al-terminar).
