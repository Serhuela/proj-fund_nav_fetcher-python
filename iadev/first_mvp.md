# Primer MVP: registrar datos de un fondo

**Objetivo:** obtener y guardar en PostgreSQL el valor liquidativo y su fecha
para un único fondo, y después automatizar su recogida en producción.

Avanzar en orden, un paso cada vez. Marcar cada punto solo cuando se haya
comprobado su resultado.

## Pasos

- [x] **1. Verificar una fuente real.** Elegir un fondo y localizar una fuente
  accesible con su valor liquidativo, fecha y divisa. Confirmar que corresponde
  al ISIN y a la clase elegidos; un folleto no es una fuente de precios.

- [x] **2. Preparar desarrollo.** Ejecutar los SQL existentes en la base de
  desarrollo y registrar manualmente el fondo, su proveedor y su asociación.
  Comprobar los registros y sus relaciones desde DBeaver.
  Creación, carga y relaciones comprobadas por el usuario en DBeaver el **18/10/2026**.

- [ ] **3. Consultar desde Python.** Hacer una única consulta a la fuente y
  mostrar el valor liquidativo, la fecha y la divisa. Contrastarlos con la fuente,
  sin bucles ni planificación periódica.

- [ ] **4. Guardar el primer dato.** Conectar la consulta con la persistencia y
  comprobar la fila en DBeaver. Repetir la ejecución y verificar que no duplica
  el mismo dato. Conservar la precisión decimal del valor liquidativo.

- [ ] **5. Ejecutar una vez en producción.** Preparar las tablas y el catálogo
  mínimo, proporcionar las credenciales DML al contenedor y ejecutar una recogida
  puntual. Comprobar el dato guardado sin dar permisos DDL al bot.

- [ ] **6. Automatizar la recogida.** Configurar la ejecución periódica y dejar
  el bot funcionando con Docker Compose. Verificar que recoge un dato posterior
  cuando la fuente lo publica y que los fallos quedan registrados en los logs.

## Carga manual del paso 2

Para hacerlo desde la terminal, usar los bloques de creación y carga de
[la guía de base de datos de desarrollo](../ops/dev/base_datos_desarrollo.md). Los ejecuta el usuario;
el agente solo consulta la base. DBeaver permite comprobar el resultado.

Trabajar únicamente contra la base de **desarrollo**:

1. Con el usuario DDL, crear las tablas siguiendo el
   [orden de los SQL](../data_model/README_data_model.md). Sustituir
   `[SCHEMA_PLACEHOLDER]` por el esquema de desarrollo existente. No ejecutar
   de nuevo los scripts sobre tablas ya creadas.
2. Con el usuario DML, importar [funds.csv](../rsc/first_mvp/funds.csv) en `funds`
   y [data_sources.csv](../rsc/first_mvp/data_sources.csv) en `data_sources`.
   En DBeaver: UTF-8, separador coma, cabecera y comillas dobles. Mapear por nombre
   a tablas existentes, sin recrearlas ni vaciarlas. No mapear `id`: PostgreSQL
   lo genera. Confirmar los cambios y comprobar ambas filas.
3. Importar la asociación desde [fund_sources.csv](../rsc/first_mvp/fund_sources.csv).
   El fichero usa `fund_isin` y `source_code`; el importador debe resolver esas
   claves a los IDs del entorno antes de insertar. El comando `load fund_sources`
   realiza esa resolución y rechaza referencias inexistentes. Comprobar la
   asociación resultante.

Si el fondo o el proveedor ya existen, utilizar sus IDs y no volver a importar
la fila. El paso 2 se completa después de importar y comprobar la asociación;
la tabla `fund_navs` permanece vacía hasta el paso 4.

## Resultado del paso 1

Comprobación técnica realizada el **18/10/2026**:

| Dato | Elección o resultado |
| --- | --- |
| Fondo | ING DIRECT FONDO NARANJA STANDARD & POOR'S 500, FI |
| ISIN | `ES0152769032` |
| Divisa | EUR |
| Proveedor elegido para el MVP | Quefondos, de VDOS |
| Valor liquidativo observado | 45,507708 EUR |
| Fecha de valoración publicada | 15/10/2026 |

**Fuente:** [ficha de Quefondos](https://www.quefondos.com/es/fondos/ficha/index.html?isin=ES0152769032).

- Una consulta puntual desde Python devolvió HTTP 200 y permitió extraer el
  ISIN, el valor, la divisa y la fecha del HTML, sin sesión ni JavaScript.
- Se elige esta ficha por su accesibilidad técnica y precisión decimal. La página
  de Amundi consultada no mostró el valor en el HTML inicial; Financial Times
  mostró el mismo dato redondeado a dos decimales.
- El valor anterior es una muestra de la verificación, no un dato que deba
  fijarse en el código. Cada recogida debe leer lo publicado en ese momento.
- Antes de automatizar consultas periódicas, confirmar las condiciones de uso
  aplicables. Revisar [el aviso legal](https://www.quefondos.com/legal.html) y las
  condiciones de VDOS que este referencia: acceso público no equivale a permiso
  para automatizar. La comprobación técnica no resuelve ese punto.

### Las dos fechas del dato

El esquema y el modelo existentes ya contemplan ambas:

- **`nav_date`:** fecha de valoración publicada por la fuente (`15/10/2026` en
  la muestra). No sustituirla por el día de la descarga.
- **`fetched_at`:** instante real en que se recoge el dato, con zona horaria;
  `FundNav` lo normaliza a UTC. El código de recogida debe capturarlo y enviarlo
  al guardar el dato, sin depender del instante por defecto de la inserción.

Referencias: [tabla fund_navs](../data_model/04_fund_navs.sql) y
[modelo FundNav](../code/models/fund_nav.py). La clave sigue siendo fondo y fecha
de valoración; guardar ambas fechas no implica guardar una fila por cada consulta.

## Fuera de este MVP

Más fondos, migradores de esquema, importadores CSV, nuevos pipelines y
abstracciones que no necesite este recorrido. Reutilizar el código existente
y añadir solo lo imprescindible para completar cada paso.

**Primer hito:** una fila real en desarrollo. **MVP completo:** recogida
periódica comprobada en producción para ese mismo fondo.
