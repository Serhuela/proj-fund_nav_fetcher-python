# Credenciales de desarrollo

Esta carpeta reúne la configuración y las herramientas para cargar en la
terminal las credenciales del entorno de desarrollo desde Bitwarden. Permite
seleccionar las credenciales de los roles de base de datos usados por la
aplicación y por las operaciones administrativas.

`bitwarden_items.json` identifica los elementos y campos que se consultan en
Bitwarden. `load_dev_env.sh` los lee y exporta sus valores como variables de
entorno en la sesión de Bash donde se carga con `source`.

Para configurar el inventario, cargar las credenciales, resolver problemas de
sesión o retirarlas al terminar, consulta la
[guía de gestión de credenciales](gestion_credenciales.md).
