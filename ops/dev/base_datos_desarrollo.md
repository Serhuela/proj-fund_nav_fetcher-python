# Gestionar la base de datos de desarrollo

Guía para crear tablas, cargar el catálogo y limpiar la base de datos de
desarrollo existente. Los comandos gestionan sus tablas y datos; la base y el
esquema deben estar creados y ser accesibles.

## Preparar la terminal

Ejecuta los comandos desde la **raíz del repositorio**, con el
[entorno de desarrollo preparado](entorno_desarrollo.md):

```bash
source .venv/bin/activate
export APP_ENV=development
```

En esa misma terminal, sigue la guía para
[cargar las credenciales de desarrollo](credentials/gestion_credenciales.md#cargar-credenciales).
La carga exporta las credenciales DDL y DML. Los comandos de `app.database_cli`
requieren ambas: preparan una conexión y un servicio para cada rol antes de
ejecutar la operación seleccionada. Estos comandos rechazan cualquier entorno
distinto de `development` y cualquier base distinta
de `psql_ddbb_dev_fund_nav`. El esquema por defecto es `nav`.

Los ejemplos indican `--schema nav` para fijar expresamente el destino. Para
trabajar en otro esquema de desarrollo, sustituye `nav` por su nombre.

## Crear todas las tablas

Ejecuta el bloque completo cuando las cuatro tablas todavía no existen.
`create` recibe una tabla por comando; la secuencia respeta sus dependencias.
Cada comando confirma su propia creación. Si uno falla, `&&` detiene la cadena;
las tablas creadas por los comandos anteriores se conservan.

```bash
python -m app.database_cli create funds --schema nav &&
python -m app.database_cli create data_sources --schema nav &&
python -m app.database_cli create fund_sources --schema nav &&
python -m app.database_cli create fund_navs --schema nav
```

## Cargar todas las tablas del catálogo MVP

Ejecuta el bloque completo después de crear las tablas. Carga los tres CSV de
`rsc/first_mvp/`: primero fondos y proveedores, y después sus asociaciones.
`load` recibe una tabla y un CSV por comando, y cada carga tiene su propia
transacción. Si una falla, `&&` detiene la cadena y las cargas anteriores se
conservan. Repetir una carga idéntica no duplica filas: las existentes se
cuentan como omitidas. Sus valores se conservan aunque el CSV contenga valores
distintos.

```bash
python -m app.database_cli load funds rsc/first_mvp/funds.csv --schema nav &&
python -m app.database_cli load data_sources rsc/first_mvp/data_sources.csv --schema nav &&
python -m app.database_cli load fund_sources rsc/first_mvp/fund_sources.csv --schema nav
```

El CSV de asociación es `rsc/first_mvp/fund_sources.csv`: enlaza por ISIN y
código de proveedor, no por IDs generados. El servicio resuelve esas dos
claves contra `funds` y `data_sources`. Si falta un fondo o proveedor, se
rechaza la carga de asociaciones y se revierte completa. La tabla `fund_navs`
queda creada y vacía: los CSV del catálogo no incluyen valores liquidativos.
Esta tabla almacena los valores obtenidos en las recogidas diarias.

La importación es aditiva: no elimina filas ausentes ni actualiza registros
existentes. El resultado informa de filas añadidas y omitidas por conflictos de
unicidad, incluidos los duplicados dentro del propio CSV. Un dato inválido o una
referencia inexistente hace fallar la carga completa y provoca su reversión.

## Limpiar

Cada comando pide escribir `psql_ddbb_dev_fund_nav.nav`. Solo ejecuta el bloque
que quieras; confirma el destino antes de continuar.

Vaciar solo valores liquidativos:

```bash
python -m app.database_cli truncate fund_navs --schema nav
```

Vaciar las cuatro tablas y reiniciar sus IDs:

```bash
python -m app.database_cli truncate fund_navs fund_sources funds data_sources --schema nav
```

Eliminar las tablas y vistas ordinarias, conservando el esquema:

```bash
python -m app.database_cli clear --schema nav
```

La última opción inspecciona el esquema y elimina tablas ordinarias/particionadas
y vistas ordinarias, sin `CASCADE`. Conserva el esquema y sus permisos. Si hay
dependencias que impiden borrar esos objetos, la transacción falla y se revierte.
No elimina vistas materializadas ni otros tipos de objetos.

## Al terminar

Sigue los pasos para [retirar las credenciales de la terminal y bloquear Bitwarden](credentials/gestion_credenciales.md#al-terminar).
