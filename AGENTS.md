# Convenciones del proyecto

Estas convenciones se aplican a todo el repositorio.

## Comunicación

- Al explicar código o diseño, empezar con una visión general breve y concreta: propósito y responsabilidades principales. Desarrollar los detalles cuando el usuario los pida.


## Restricciones obligatorias de Git y GitHub

- El agente solo puede realizar operaciones de lectura en Git y GitHub.
- Está prohibido crear, editar, eliminar o modificar cualquier contenido o estado en GitHub, aunque la CLI `gh` esté instalada y autenticada. Esta restricción se aplica también a las API, MCP, interfaces web y cualquier otra herramienta.
- Está prohibido ejecutar operaciones de Git que modifiquen el estado local o remoto, incluidos `git add`, `git commit`, `git pull`, `git push`, `git fetch`, `git merge`, `git rebase`, `git checkout`, `git switch`, `git reset`, `git stash`, `git clean`, `git config` y la creación o eliminación de ramas o etiquetas.
- Solo se permiten consultas de lectura, como `git status`, `git diff`, `git log`, `git show` y consultas de GitHub que no produzcan cambios.
- Cuando una petición requiera modificar Git o GitHub, el agente debe proporcionar las instrucciones o comandos para que los ejecute personalmente el usuario; nunca debe ejecutarlos por su cuenta.

## Entorno virtual y dependencias

- El agente no debe crear, recrear ni modificar el entorno virtual del proyecto (`.venv/`). En particular, no debe instalar, actualizar, desinstalar ni sincronizar paquetes en ese entorno, ni ejecutar comandos o tareas que lo hagan indirectamente.
- Si una tarea requiere cambiar dependencias, el agente puede actualizar los archivos declarativos del proyecto, como `pyproject.toml`, y debe proporcionar al usuario los comandos exactos para que él los ejecute en su entorno virtual.
- Si falta una dependencia para ejecutar o verificar algo, el agente debe indicarlo y dar el comando de instalación correspondiente; no debe instalarla por su cuenta.

## Documentación del código

- Los comentarios y los docstrings del código se escriben en castellano.
- Los ficheros, las clases, las funciones y los métodos deben incluir docstrings que expliquen su propósito y, cuando corresponda, sus parámetros, resultados, excepciones, efectos secundarios y limitaciones. Los docstrings de funciones y métodos siguen el estilo Google para Python: incluyen `Args:` para los parámetros, `Returns:` para el valor devuelto, `Raises:` para las excepciones y `Yields:` para los valores producidos por los generadores, según corresponda. Deben cubrir todos los parámetros y resultados relevantes, omitir las secciones que no apliquen y conservar estas etiquetas estándar en inglés, con el contenido en castellano.

## Legibilidad del código

- Priorizar la legibilidad para las personas en todo el código, no solo en los mensajes. Preferir nombres descriptivos, un flujo de ejecución claro y pasos explícitos frente a expresiones densas, trucos de lenguaje o microoptimizaciones que dificulten entender la intención. No sacrificar la corrección ni la seguridad por legibilidad.
- Dividir las expresiones complejas en pasos con variables intermedias cuando ayude a comprenderlas. Evitar tanto comprimir varias responsabilidades en una línea como añadir abstracciones o fragmentar el código sin un beneficio claro de comprensión. Los comentarios explican la intención y las decisiones; no sustituyen un código claro.
- Al construir cualquier string con valores variables, usar f-strings en lugar de interpolación con `%`, `.format()` o concatenaciones para insertar esos valores. Esta norma incluye mensajes de `print`, logs y excepciones; en los logs, pasar el mensaje ya construido con una f-string, no una plantilla con argumentos separados.
- Los strings sin valores variables siguen siendo literales normales; no añadir el prefijo `f` si no hay interpolación.
- La norma de f-strings no se aplica a la composición de consultas SQL: mantener los valores parametrizados y los identificadores compuestos con las herramientas del controlador. No interpolar datos ni identificadores SQL mediante f-strings.

## Tests

- Cada fichero de tests debe incluir al principio un resumen que indique qué fichero de código verifica, qué comportamientos cubre y cuáles quedan fuera de su alcance.
- La carpeta `tests/` se organiza por tipo de prueba, por ejemplo `unitarios/` e `integracion/`. Dentro de cada tipo se replica la estructura de subcarpetas de `code/`.
- En la medida de lo posible, cada fichero de tests verifica un único fichero de código.
- El fichero de tests conserva el nombre del fichero de código y añade `_test` antes de la extensión. Por ejemplo, `code/app/application.py` corresponde a `tests/unitarios/app/application_test.py` y, cuando haya pruebas de integración para ese fichero, a `tests/integracion/app/application_test.py`.

## Documentación

- Los README explican de forma concreta y concisa para qué sirve la carpeta que los contiene y cómo trabajar con ella. Su funcionalidad es independiente de que esté vacía o de que su implementación esté completa.
- Los README describen ese propósito y uso en presente; no son informes de avance ni listas de pendientes, previsiones o funcionalidades ausentes. Esta redacción se mantiene cuando el README se crea antes que el contenido.
- Se pueden listar ficheros y subcarpetas cuando ayude a comprender el propósito de la carpeta, orientarse o usar su contenido; no es obligatorio hacerlo. La documentación específica de cada fichero, clase o método va en el propio fichero, mediante comentarios o docstrings cuando proceda.
- Cada README se limita al ámbito de su carpeta. Cuando mencione subcarpetas, incluye una descripción breve y un enlace a su README si existe; sus detalles e instrucciones específicas van en el README de la subcarpeta, sin duplicarlos en el de la carpeta superior.
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

## Fuentes y artefactos generados

- Editar la fuente y generar desde ella cualquier artefacto compilable o derivado con su herramienta correspondiente. No crear ni modificar manualmente esos artefactos, tampoco con IA.
- Ejemplos: editar los ficheros `.tex` y compilar el PDF; editar los `.drawio` y exportar los SVG con Draw.io. Tras modificar una fuente, regenerar sus artefactos derivados para que queden sincronizados.
- Si el compilador o exportador necesario no está disponible, informar al usuario y esperar instrucciones para disponer de la herramienta. No sustituirla por una edición manual ni instalar software por cuenta propia.

## Diagramas Draw.io

- Cada archivo `.drawio` debe tener una exportación `.svg` en la misma carpeta y con el mismo nombre base. Por ejemplo, `arquitectura.drawio` debe ir acompañado de `arquitectura.svg`.
- Al modificar un `.drawio`, hay que actualizar también su SVG para que ambos representen el mismo diagrama.
