# Gestionar las credenciales de desarrollo

Carga de credenciales desde Bitwarden en la terminal del entorno de desarrollo.

Requisitos: Bash, [Bitwarden CLI (`bw`)](https://bitwarden.com/help/cli/) y `jq`.

## Cargar credenciales

Desde la raíz del repositorio:

```bash
bw login # Solo si todavía no has iniciado sesión
export BW_SESSION="$(bw unlock --raw)"
bw sync
source ops/dev/credentials/load_dev_env.sh
```

## Si Bitwarden informa que no encuentra un elemento

Si `load_dev_env.sh` no puede leer un elemento, comprueba si la sesión está
activa y la bóveda desbloqueada. El script usa `--nointeraction`, por lo que no
pedirá la contraseña maestra: si la sesión no sirve, fallará. Inicia sesión si
hace falta, desbloquea la bóveda y exporta el token de sesión en la misma terminal:

```bash
bw login # Solo si todavía no has iniciado sesión
export BW_SESSION="$(bw unlock --raw)" # Introduce la contraseña maestra si la solicita
bw status --session "$BW_SESSION" | jq -r '.status'
```

Continúa solo cuando el estado sea `unlocked`; después, vuelve a cargar las
credenciales con `source ops/dev/credentials/load_dev_env.sh`. `bw login` inicia
sesión en el CLI y `BW_SESSION` contiene la clave temporal para usar la bóveda
desbloqueada. Si sigue fallando, verifica que el ID del elemento y los campos
configurados sean correctos.

## Obtener los IDs para configurar el inventario

Al crear [bitwarden_items.json](bitwarden_items.json), busca los IDs de los elementos de deploy y bot con la sesión de Bitwarden desbloqueada:

```bash
bw list items --search "fund_nav_fetcher" | jq -r '.[] | [.id, .name] | @tsv'
```

Copia cada ID como clave de su entrada correspondiente en `bitwarden_items.json`.

## Al terminar

```bash
unset BBDD_DEPLOY_USERNAME BBDD_DEPLOY_PASSWORD BBDD_BOT_USERNAME BBDD_BOT_PASSWORD
bw lock
unset BW_SESSION
```
