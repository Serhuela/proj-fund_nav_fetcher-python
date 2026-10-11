# Operaciones de desarrollo

En esta carpeta se encuentran las operaciones del entorno de desarrollo local.

## Contenido

- [credentials/](credentials/README_credentials.md): carga de credenciales para desarrollo.

## Descargar el repositorio

Estos comandos están preparados para Linux o WSL, con Git y `pyenv` instalados.

```bash
git clone https://github.com/Serhuela/proj-fund_nav_fetcher-python.git
cd proj-fund_nav_fetcher-python
```

## Crear el entorno e instalar las dependencias

Desde la raíz del repositorio, instala Python 3.13.7 y crea el entorno virtual
en `.venv/`. La versión está seleccionada en el archivo `.python-version`.

```bash
pyenv install -s 3.13.7
pyenv exec python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e . --group dev
```

La instalación editable permite trabajar con el código sin reinstalarlo tras
cada cambio. También instala las dependencias de ejecución y el grupo `dev`
de `pyproject.toml`. La opción `--group` requiere pip 25.1 o posterior.

En las siguientes sesiones, activa el entorno desde la raíz del repositorio:

```bash
source .venv/bin/activate
```

## Ejecutar la aplicación

Con el entorno activado:

```bash
APP_ENV=development python -m app.main
```

## Ejecutar los tests

Desde la raíz del repositorio, con el entorno activado:

```bash
python -m pytest
```

La configuración de `pyproject.toml` ejecuta las pruebas en paralelo, muestra la
cobertura en la terminal y genera el informe HTML en `htmlcov/index.html`.
