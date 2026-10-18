# Pruebas

Pruebas automatizadas para verificar el comportamiento del código del proyecto.

Las pruebas conservan el nombre del fichero de código y añaden `_test`.
Se organizan por tipo de prueba, replicando las carpetas de `code/`.

Las pruebas unitarias usan dobles para aislar el acceso a datos; las de
integración comprueban el comportamiento contra PostgreSQL con tablas temporales.

Desde la raíz, con el entorno ya preparado:

```bash
python -m pytest
```

Para una ejecución sencilla sin paralelismo ni informes de cobertura:

```bash
python -m pytest -o addopts='' --import-mode=importlib -m 'not integration'
```

La integración usa `Configuration`: los parámetros de `code/utils/config.yaml`
y sus sobrescrituras de entorno. Carga `BBDD_BOT_USERNAME` y `BBDD_BOT_PASSWORD`
en el entorno siguiendo la [gestión de credenciales](../ops/dev/credentials/gestion_credenciales.md#cargar-credenciales).
El rol necesita permiso `TEMPORARY` en la base de desarrollo.

La fixture `empty_postgres` abre una conexión sin crear tablas de prueba. La fixture
`postgres_with_tables_in_temporary_schema` se apoya en ella y prepara las tablas
`funds`, `data_sources`, `fund_sources` y `fund_navs` vacías en el esquema temporal
de la conexión. Cada test solicita el escenario que necesita y añade expresamente
sus propios datos.

Para incluir también la integración:

```bash
APP_ENV=development python -m pytest -m ''
```

Para ejecutar solo la integración, usa `APP_ENV=development python -m pytest -m integration`.
La preparación rechaza cualquier entorno distinto de `development` y cualquier
base distinta de `psql_ddbb_dev_fund_nav`. La configuración incompleta y los errores
de conexión hacen fallar la preparación de las pruebas; no se omiten.

Cada prueba usa su propia conexión y tablas temporales que se eliminan al cerrarla;
no modifica tablas permanentes. No necesita que el esquema de la aplicación esté desplegado.
