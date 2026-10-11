#!/usr/bin/env bash
# Sincroniza los secretos de Actions del repositorio con la lista de esta carpeta.
# Uso: bash ops/credentials/configure_github_secrets.sh
# Solicita valores ocultos; Enter conserva un secreto existente. Para la clave
# SSH solicita un archivo y envía su contenido completo, incluidos los saltos de línea.
# Tras completar los prompts ofrece borrar los secretos fuera de la lista,
# con una confirmación general (por defecto no) y otra por secreto (por defecto sí).
# Requiere Bash 4+, jq, gh autenticado y permisos para administrar secretos del repo.
# No consulta valores remotos. Ante un fallo, termina sin continuar: las escrituras
# previas no se revierten y el borrado no empieza hasta completar todos los prompts.

set +x
set -euo pipefail

REPOSITORY="Serhuela/proj-fund_nav_fetcher-python"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SECRETS_FILE="${SCRIPT_DIR}/github_actions_secrets.json"

# Informa del error sin mostrar valores de los secretos y termina la ejecución.
fail() {
    printf 'Error: %s\n' "$1" >&2
    exit 1
}

# Pregunta sí/no con el valor por defecto indicado; devuelve 0 para sí y 1 para no.
# Repite respuestas inválidas y termina el script ante una entrada interrumpida.
confirm() {
    local prompt="$1" default="$2" answer options
    if [[ "$default" == yes ]]; then
        options="S/n"
    else
        options="s/N"
    fi
    while true; do
        printf '%s [%s]: ' "$prompt" "$options"
        IFS= read -r answer || fail "Entrada interrumpida; se detiene el borrado."
        case "${answer,,}" in
            s|si|sí|y|yes) return 0 ;;
            n|no) return 1 ;;
            "") [[ "$default" == yes ]] && return 0; return 1 ;;
            *) printf 'Responde s o n, o pulsa Enter para la opción por defecto.\n' ;;
        esac
    done
}

command -v gh >/dev/null 2>&1 || fail "Falta GitHub CLI (gh)."
command -v jq >/dev/null 2>&1 || fail "Falta jq para leer la configuración JSON."
[[ -r "$SECRETS_FILE" ]] || fail "No se puede leer $SECRETS_FILE."

# Valida el JSON completo antes de acceder a GitHub para evitar borrados por errores.
jq -e '
    type == "array" and length > 0 and
    all(.[];
        type == "object" and
        (.name | type == "string" and test("^[A-Z_][A-Z0-9_]*$")) and
        (.description | type == "string" and test("\\S")) and
        (.type == "standard" or .type == "ssh_key")
    )
' "$SECRETS_FILE" >/dev/null || fail "El JSON debe contener una lista no vacía con name, description y type (standard o ssh_key) válidos."
entries="$(jq -c '.[]' "$SECRETS_FILE")"
declare -a required=()
declare -A wanted=()
declare -A descriptions=()
declare -A secret_types=()
while IFS= read -r entry; do
    name="$(jq -r '.name' <<< "$entry")"
    description="$(jq -r '.description' <<< "$entry")"
    [[ -z "${wanted[$name]:-}" ]] || fail "Nombre duplicado en la lista: $name."
    required+=("$name")
    wanted["$name"]=1
    descriptions["$name"]="$description"
    secret_types["$name"]="$(jq -r '.type' <<< "$entry")"
done <<< "$entries"

gh auth status >/dev/null 2>&1 || fail "Inicia sesión con gh auth login."
existing_names="$(gh secret list --repo "$REPOSITORY" --app actions --json name --jq '.[].name')"
declare -A existing=()
while IFS= read -r name; do
    if [[ -n "$name" ]]; then
        existing["$name"]=1
    fi
done <<< "$existing_names"

printf 'Repositorio: %s\nLista: %s\n' "$REPOSITORY" "$SECRETS_FILE"
printf 'Al terminar podrás revisar el borrado de secretos de Actions fuera de la lista.\n'

for name in "${required[@]}"; do
    while true; do
        printf '\n%s: %s\n' "$name" "${descriptions[$name]}"
        if [[ "${secret_types[$name]}" == ssh_key ]]; then
            printf '\nIntroduce la ruta al archivo de clave privada SSH para %s' "$name"
        else
            printf '\nIntroduce el valor de %s' "$name"
        fi
        if [[ -n "${existing[$name]:-}" ]]; then
            printf ' (dejar vacío para mantener el valor que hay)'
        else
            printf ' (todavía no existe; obligatorio)'
        fi
        printf ': '
        IFS= read -r -s value || fail "Entrada interrumpida; no se inicia el borrado."
        printf '\n'
        if [[ -z "$value" ]]; then
            if [[ -n "${existing[$name]:-}" ]]; then
                printf 'Se mantiene %s.\n' "$name"
                break
            fi
            printf 'Este secreto no existe. Introduce un valor.\n'
            continue
        fi
        if [[ "${secret_types[$name]}" == ssh_key ]]; then
            # Admite rutas con espacios y el prefijo ~/ sin evaluar texto del usuario.
            value="${value/#\~\//$HOME/}"
            if [[ ! -f "$value" || ! -r "$value" || ! -s "$value" ]]; then
                printf 'El archivo debe existir, ser legible y no estar vacío.\n'
                continue
            fi
            gh secret set "$name" --repo "$REPOSITORY" --app actions < "$value"
        else
            printf '%s' "$value" | gh secret set "$name" --repo "$REPOSITORY" --app actions
        fi
        unset value
        printf 'Guardado %s.\n' "$name"
        break
    done
done

# Solo administra secretos de Actions a nivel de repositorio, sin tocar otros ámbitos.
declare -a obsolete=()
while IFS= read -r name; do
    [[ -z "$name" || -n "${wanted[$name]:-}" ]] && continue
    obsolete+=("$name")
done <<< "$existing_names"

if [[ ${#obsolete[@]} -gt 0 ]]; then
    printf '\nSecretos fuera de la lista:\n'
    printf '  - %s\n' "${obsolete[@]}"
    if confirm '¿Quieres proceder con el borrado?' no; then
        for name in "${obsolete[@]}"; do
            if confirm "¿Borrar el secreto $name?" yes; then
                gh secret delete "$name" --repo "$REPOSITORY" --app actions
                printf 'Eliminado %s.\n' "$name"
            else
                printf 'Se conserva %s.\n' "$name"
            fi
        done
    else
        printf 'Borrado cancelado; se conservan los secretos fuera de la lista.\n'
    fi
fi
printf '\nConfiguración de secretos completada.\n'
