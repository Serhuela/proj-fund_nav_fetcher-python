# Diseño

Diagramas de arquitectura y del diseño de clases del proyecto. Las fuentes
editables están en formato `.drawio` y sus vistas previas en formato SVG.

- [Arquitectura](arquitectura.drawio): aplicación, fuentes externas y PostgreSQL;
  [vista SVG](arquitectura.svg).
- [Clases](diagrama_clases.drawio): responsabilidades y relaciones del acceso a
  datos; [vista SVG](diagrama_clases.svg).

## Exportar los diagramas a SVG

Edita el `.drawio` y genera su SVG con Draw.io. No edites el SVG manualmente.

Desde la raíz del repositorio, con Draw.io Desktop instalado:

```bash
drawio -x -f svg -o "design/arquitectura.svg" "design/arquitectura.drawio"
drawio -x -f svg -o "design/diagrama_clases.svg" "design/diagrama_clases.drawio"
```

En la interfaz gráfica, abre el `.drawio` y selecciona **File > Export as > SVG**.
Guarda el SVG en la misma carpeta y con el mismo nombre base que la fuente.
