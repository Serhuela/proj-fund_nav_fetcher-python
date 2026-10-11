# Credenciales de desarrollo

Requisitos: Bash, [Bitwarden CLI (`bw`)](https://bitwarden.com/help/cli/) y `jq`.

## Cargar credenciales

Desde la raíz del repositorio:

```bash
bw login # Solo si todavía no has iniciado sesión
export BW_SESSION="$(bw unlock --raw)"
bw sync
source ops/dev/credentials/load_dev_env.sh
```

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
