# Convenciones del proyecto

Estas convenciones se aplican a todo el repositorio.

## Restricciones obligatorias de Git y GitHub

- El agente solo puede realizar operaciones de lectura en Git y GitHub.
- Está prohibido crear, editar, eliminar o modificar cualquier contenido o estado en GitHub, aunque la CLI `gh` esté instalada y autenticada. Esta restricción se aplica también a las API, MCP, interfaces web y cualquier otra herramienta.
- Está prohibido ejecutar operaciones de Git que modifiquen el estado local o remoto, incluidos `git add`, `git commit`, `git pull`, `git push`, `git fetch`, `git merge`, `git rebase`, `git checkout`, `git switch`, `git reset`, `git stash`, `git clean`, `git config` y la creación o eliminación de ramas o etiquetas.
- Solo se permiten consultas de lectura, como `git status`, `git diff`, `git log`, `git show` y consultas de GitHub que no produzcan cambios.
- Cuando una petición requiera modificar Git o GitHub, el agente debe proporcionar las instrucciones o comandos para que los ejecute personalmente el usuario; nunca debe ejecutarlos por su cuenta.

## Documentación del código

- Los comentarios y los docstrings del código se escriben en castellano.
- Hay que documentar los ficheros, las clases, las funciones, los métodos, etc. La documentación debe explicar su propósito y, cuando corresponda, sus parámetros, resultados, excepciones lanzadas, efectos secundarios y limitaciones.

## Tests

- Cada fichero de tests debe incluir al principio un resumen que indique qué fichero de código verifica, qué comportamientos cubre y cuáles quedan fuera de su alcance.
- La carpeta `tests/` se organiza por tipo de prueba, por ejemplo `unitarios/` e `integracion/`. Dentro de cada tipo se replica la estructura de subcarpetas de `code/`.
- En la medida de lo posible, cada fichero de tests verifica un único fichero de código.
- El fichero de tests conserva el nombre del fichero de código y añade `_test` antes de la extensión. Por ejemplo, `code/app/application.py` corresponde a `tests/unitarios/app/application_test.py` y, cuando haya pruebas de integración para ese fichero, a `tests/integracion/app/application_test.py`.

## Documentación

- Los README describen lo que hay en el repositorio o en su carpeta y explican cómo trabajar con ese contenido. Los README's describen como usar el presente repositorio.
- Cada README se limita al contenido de su propia carpeta. Para las subcarpetas, incluye una descripción breve y un enlace a su README; los detalles de sus archivos y las instrucciones de uso van en el README de la subcarpeta, sin duplicarlos en el de la carpeta superior.
- La documentación LaTeX en `documentation/LaTeX/` es la memoria técnica completa del proyecto: objetivo, alcance, diseño, arquitectura, modelo de datos y decisiones técnicas.
- La página web en `docs/` contiene lo que se decida exponer al público. Su contenido se selecciona para presentar el proyecto y no tiene que describirlo por completo.

## Nombres de los README

- El README de la raíz se llama exactamente `README.md`.
- En cualquier otra carpeta, el README se llama `README_<nombre_de_la_última_carpeta>.md`: el prefijo `README` va en mayúsculas, seguido de un guion bajo y del nombre exacto de la carpeta que contiene el archivo.
- Esta convención permite distinguir los README al abrirlos en Visual Studio Code.

Ejemplos:

| Ubicación | Nombre |
| --- | --- |
| Raíz del repositorio | `README.md` |
| `design/` | `README_design.md` |
| `data_model/` | `README_data_model.md` |
| `documentation/LaTeX/` | `README_LaTeX.md` |
| `ops/` | `README_ops.md` |
| `code/` | `README_code.md` |
| `tests/` | `README_tests.md` |

Estos ejemplos establecen los nombres cuando se necesite un README; no obligan a crear uno en cada carpeta.

## Diagramas Draw.io

- Cada archivo `.drawio` debe tener una exportación `.svg` en la misma carpeta y con el mismo nombre base. Por ejemplo, `arquitectura.drawio` debe ir acompañado de `arquitectura.svg`.
- Al modificar un `.drawio`, hay que actualizar también su SVG para que ambos representen el mismo diagrama.
