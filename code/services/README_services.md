# Servicios de datos

`DataService` es la interfaz entre los bots y la base de datos. Todas las
operaciones de acceso a datos de los bots pasan por este servicio, que coordina
los repositorios y se responsabiliza del `commit` o `rollback` al finalizar
cada operación. Los repositorios contienen el SQL y dejan la decisión
transaccional al servicio.

`SchemaAdminService` concentra el DDL y debe recibir una conexión con permisos
administrativos; el bot no construye este servicio.

Ambos reciben una instancia dedicada de `Postgres`. `app.database_cli` es la
entrada para las operaciones manuales de desarrollo y selecciona credenciales
distintas para DML y DDL. El llamador cierra la conexión al terminar.
