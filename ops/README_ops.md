# Operaciones

En esta carpeta se encuentra todo lo relativo a las operaciones del proyecto.

## Contenido

- [credentials/](credentials/README_credentials.md): lista y carga interactiva de secretos de GitHub Actions.
- [docker/](docker/README_docker.md): archivos para construir la imagen y ejecutar el contenedor Docker.
- [dev/](dev/README_dev.md): preparación del entorno y herramientas de desarrollo.

## Primer despliegue a producción

Al crear el repositorio, antes del primer despliegue a producción, hay que cargar
los secretos de GitHub Actions. En [credentials/](credentials/README_credentials.md)
se encuentran la lista de secretos necesarios y el script para cargarlos.

## Instalación de producción sin Docker

En Linux o WSL, con `pyenv` instalado y el repositorio descargado, ejecuta desde
la raíz del repositorio:

```bash
pyenv install -s 3.13.7
pyenv exec python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
```

El entorno virtual queda en `.venv/`, en la raíz del repositorio.
`python -m pip install .` instala la aplicación y las dependencias de producción
indicadas en `pyproject.toml`, sin añadir el grupo `dev`.

Para arrancar la aplicación con el entorno activado:

```bash
APP_ENV=production python -m app.entrypoint
```

La aplicación se ejecuta en primer plano. En el despliegue con Docker, la imagen
se encarga de instalar las dependencias y configurar el arranque.
