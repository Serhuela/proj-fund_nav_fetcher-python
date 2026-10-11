# Imagen de producción: instala el paquete y ejecuta su punto de entrada.
# Construir desde la raíz: docker build -f ops/docker/Dockerfile -t fund-nav-fetcher:local .
FROM python:3.13-slim

# Identifica el entorno de ejecución para la aplicación.
ENV APP_ENV=production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instala únicamente las dependencias de ejecución declaradas en pyproject.toml.
COPY pyproject.toml README.md ./
COPY code/ ./code/
RUN pip install --no-cache-dir . \
    && useradd --create-home --uid 10001 app

# El servicio no necesita permisos de administrador ni puertos publicados.
USER app
CMD ["python", "-m", "app.entrypoint"]
