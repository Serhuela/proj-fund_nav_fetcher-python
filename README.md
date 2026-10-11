# proj-fund_nav_fetcher-python

Obtención y almacenamiento de valores liquidativos (NAV) de fondos de inversión para su consulta posterior.

## Estructura del repositorio

Las carpetas principales y su contenido son:

```text
.
├── .github/workflows/     # Automatización con GitHub Actions.
├── code/                 # Código Python de la aplicación.
│   ├── app/              # Arranque y lógica de la aplicación.
│   └── utils/            # Utilidades compartidas.
├── tests/                # Pruebas del proyecto, organizadas por tipo.
│   └── unitarios/        # Pruebas unitarias.
├── ops/                  # Entornos, credenciales, instalación y despliegue.
├── design/               # Diagramas de arquitectura.
├── data_model/           # Definiciones SQL y diagramas del modelo de datos.
├── documentation/        # Documentación técnica del proyecto.
│   └── LaTeX/            # Memoria técnica: fuentes LaTeX y PDF.
└── docs/                 # Página pública del proyecto.
```

## Por dónde empezar

Antes de modificar el repositorio, consulta [AGENTS.md](AGENTS.md) y el README
de la carpeta en la que vayas a trabajar.

- Para preparar el entorno y trabajar con el código, consulta [ops/dev/](ops/dev/README_dev.md).
- Para instalar o desplegar la aplicación en producción, consulta [ops/](ops/README_ops.md).
- Para conocer el diseño y las decisiones técnicas, consulta la [memoria técnica](documentation/LaTeX/main.pdf).
- Para ver la presentación pública del proyecto, consulta [docs/](docs/index.html).

## Licencia

Consulta [LICENSE](LICENSE).
