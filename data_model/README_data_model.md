# Modelo de datos

SQL de creación para PostgreSQL. Sustituye `[SCHEMA_PLACEHOLDER]` por el nombre
del esquema existente y ejecuta, en este orden:

1. `01_funds.sql`: fondos identificados por ISIN.
2. `02_data_sources.sql`: proveedores de datos.
3. `03_fund_sources.sql`: asociaciones entre fondos y proveedores.
4. `04_fund_navs.sql`: valores liquidativos con su fuente.

Son scripts para un esquema sin estas tablas, no una migración de tablas existentes.
No contienen credenciales ni borrados en cascada.

Diagrama entidad-relación editable: [modelo_datos.drawio](modelo_datos.drawio).
Vista previa: [modelo_datos.svg](modelo_datos.svg).
