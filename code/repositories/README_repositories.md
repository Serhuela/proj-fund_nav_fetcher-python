# Repositorios

Acceso a las tablas del proyecto: consultas, inserciones e importación de
registros preparados. La base declara los atributos de clase `TABLE_NAME`,
`SQL_FILE`, `IMPORT_KEYS` e `IMPORT_COLUMNS`; cada repositorio concreto define
sus valores. La base inserta cada carga en una sola sentencia, conserva las
filas existentes y devuelve los recuentos de inserciones y omisiones.

Los repositorios reciben valores independientes de su formato de origen y dejan
el commit y el rollback al servicio. El servicio coordina las consultas para
resolver referencias entre tablas antes de importar las asociaciones.
