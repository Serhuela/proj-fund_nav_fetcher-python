#!/usr/bin/env bash

# Carga variables de entorno desde Bitwarden usando el contrato JSON local.
# Uso:
#   source ops/dev/credentials/load_dev_env.sh

command -v bw >/dev/null 2>&1 || { echo "❌ ERROR: falta 'bw'" >&2; return 1; }
command -v jq >/dev/null 2>&1 || { echo "❌ ERROR: falta 'jq'" >&2; return 1; }

_bw_session_error() {
  local msg="$1"
  printf '❌ ERROR: %s\nEjecutá primero:\n\n\texport BW_SESSION="$(bw unlock --raw)"\n\n' "${msg}" >&2
  return 1
}

# No interactivo: exige sesión BW_SESSION ya cargada.
[[ -n "${BW_SESSION:-}" ]] || { _bw_session_error "BW_SESSION no está definida"; return 1; }

# Validación real de sesión (no solo presencia): debe ser utilizable y no interactiva.
bw --nointeraction status --session "${BW_SESSION}" >/dev/null 2>&1 || { _bw_session_error "BW_SESSION inválida o expirada"; return 1; }

echo "✅ BW_SESSION válida y utilizable"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BW_ITEMS_FILE="${SCRIPT_DIR}/bitwarden_items.json"

[[ -f "${BW_ITEMS_FILE}" ]] || { echo "❌ ERROR: no existe ${BW_ITEMS_FILE}" >&2; return 1; }

items_count="$(jq 'keys | length' "${BW_ITEMS_FILE}")"
[[ "${items_count}" -gt 0 ]] || {
  echo "❌ ERROR: ${BW_ITEMS_FILE} no contiene items." >&2
  return 1
}

echo "✅ Encontrados ${items_count} items en ${BW_ITEMS_FILE}"

_bw_item_not_found_error() {
  local item_id="$1"
  local item_folder="$2"
  local item_name="$3"
  local item_description="$4"

  printf '❌ ERROR: no existe (o no tenés acceso) al item de Bitwarden con id:\n\n\t%s\n\n' "${item_id}" >&2
  echo "Item documentado:" >&2
  echo "  folder      : ${item_folder}" >&2
  echo "  name        : ${item_name}" >&2
  echo "  description : ${item_description}" >&2
  echo >&2
  echo "Comando para buscar en Bitwarden por texto:" >&2
  echo "  bw list items --search \"${item_name}\" --session \"\$BW_SESSION\" | jq -r '.[] | \"\\(.id)\\t\\(.name)\"'" >&2
  echo >&2
  echo "Sugerencias de posibles IDs:" >&2
  bw --nointeraction list items --search "${item_name}" --session "${BW_SESSION}" 2>/dev/null | jq -r '.[] | "  - \(.id)\t\(.name)"' >&2 || true
  return 1
}

_bw_field_missing_error() {
  local item_id="$1"
  local item_folder="$2"
  local item_name="$3"
  local item_description="$4"
  local source_path="$5"
  local env_var="$6"

  echo "❌ ERROR: falta field esperado en Bitwarden." >&2
  echo "  item_id : ${item_id}" >&2
  echo "  folder  : ${item_folder}" >&2
  echo "  name    : ${item_name}" >&2
  echo "  desc    : ${item_description}" >&2
  echo "  source  : ${source_path}" >&2
  echo "  env_var : ${env_var}" >&2
  return 1
}

_value_from_source() {
  local source="$1"
  local value=""
  # source puede ser:
  # 1) un path jq directo (ej: .login.username)
  # 2) un nombre de custom field de Bitwarden (ej: Namespace, bucket_name)
  if [[ "${source}" == .* ]]; then
    value="$(echo "${ITEM_JSON}" | jq -r "${source}" 2>/dev/null || true)"
  else
    value="$(echo "${ITEM_JSON}" | jq -r --arg field_name "${source}" '(.fields // [] | map(select(.name==$field_name and (.value!=null))) | .[0].value) // empty' 2>/dev/null || true)"
  fi

  [[ "${value}" == "null" ]] && value=""
  echo "${value}"
}

loaded_items=0
loaded_vars=0

# Carga campos esperados definidos en bitwarden_items.json para TODOS los items.
while IFS= read -r item_row; do
  BW_ITEM_ID="$(echo "${item_row}" | jq -r '.key')"
  ITEM_META="$(echo "${item_row}" | jq -c '.value')"

  ITEM_FOLDER="$(echo "${ITEM_META}" | jq -r '.folder // "(sin folder)"')"
  ITEM_NAME="$(echo "${ITEM_META}" | jq -r '.name // "(sin nombre)"')"
  ITEM_DESCRIPTION="$(echo "${ITEM_META}" | jq -r '.description // "(sin descripción)"')"

  if ! ITEM_JSON="$(bw --nointeraction get item "${BW_ITEM_ID}" --session "${BW_SESSION}" 2>/dev/null)"; then
    _bw_item_not_found_error "${BW_ITEM_ID}" "${ITEM_FOLDER}" "${ITEM_NAME}" "${ITEM_DESCRIPTION}"
    return 1
  fi

  echo "Cargando item: ${ITEM_NAME} (folder: ${ITEM_FOLDER})"

  item_loaded_vars=0
  while IFS= read -r row; do
    source_path="$(echo "${row}" | jq -r '.source')"
    env_var="$(echo "${row}" | jq -r '.env_var')"
    value="$(_value_from_source "${source_path}")"

    if [[ -z "${value}" ]]; then
      _bw_field_missing_error "${BW_ITEM_ID}" "${ITEM_FOLDER}" "${ITEM_NAME}" "${ITEM_DESCRIPTION}" "${source_path}" "${env_var}"
      return 1
    fi

    export "${env_var}=${value}"
    echo "  - ${env_var}=****${value: -4}"
    item_loaded_vars=$((item_loaded_vars + 1))
    loaded_vars=$((loaded_vars + 1))
  done < <(echo "${ITEM_META}" | jq -c '.expected_fields[]')

  echo "  ✅ Cargado item: ${ITEM_NAME} (env vars: ${item_loaded_vars})"
  loaded_items=$((loaded_items + 1))
done < <(jq -c 'to_entries[]' "${BW_ITEMS_FILE}")

echo
echo "✅ Variables cargadas desde Bitwarden"
echo "   items_loaded=${loaded_items}"
echo "   vars_loaded=${loaded_vars}"
echo
