#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [[ ! -f "${REPO_ROOT}/backend/package.json" ]]; then
  echo "Current directory is not a valid vue3 repo root." >&2
  exit 1
fi

APP_ROOT="${APP_ROOT:-/opt/vline-backend}"
BACKEND_ROOT="${BACKEND_ROOT:-${APP_ROOT}/backend}"
DATA_ROOT="${DATA_ROOT:-/var/lib/vline-backend}"
SERVICE_NAME="${SERVICE_NAME:-vline-backend}"
SERVICE_USER="${SERVICE_USER:-vline}"
ENV_FILE="${ENV_FILE:-/etc/vline-backend.env}"
EDGE_DEVICE_ID="${EDGE_DEVICE_BOOTSTRAP_ID:-csrpi-001}"
SUDO=''

if [[ "${EUID}" -ne 0 ]]; then
  SUDO='sudo'
fi

log() {
  echo "[check-backend-state] $*"
}

fail() {
  echo "[check-backend-state] ERROR: $*" >&2
  exit 1
}

load_runtime_env() {
  [[ -f "${ENV_FILE}" ]] || fail "environment file ${ENV_FILE} was not found"

  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a

  [[ -n "${DATABASE_URL:-}" ]] || fail "DATABASE_URL is required in ${ENV_FILE}"
  EDGE_DEVICE_ID="${EDGE_DEVICE_BOOTSTRAP_ID:-${EDGE_DEVICE_ID}}"
}

resolve_sqlite_path() {
  local raw_path
  raw_path="${DATABASE_URL#file:}"
  raw_path="${raw_path%%\?*}"
  raw_path="${raw_path%\"}"
  raw_path="${raw_path#\"}"

  [[ -n "${raw_path}" ]] || fail "DATABASE_URL must use file:/path/to/db format"

  if [[ "${raw_path}" = /* ]]; then
    DB_PATH="${raw_path}"
    return
  fi

  DB_PATH="${BACKEND_ROOT}/prisma/${raw_path#./}"
}

ensure_tools() {
  command -v sqlite3 >/dev/null 2>&1 || fail "sqlite3 is required; install it or run scripts/bootstrap-backend.sh"
  command -v systemctl >/dev/null 2>&1 || fail "systemctl is required on the deployment host"
  [[ -d "${BACKEND_ROOT}" ]] || fail "backend directory ${BACKEND_ROOT} was not found"
  [[ -f "${BACKEND_ROOT}/package.json" ]] || fail "backend package.json was not found in ${BACKEND_ROOT}"
}

sql_value() {
  sqlite3 "${DB_PATH}" "$1" 2>/dev/null || true
}

sql_escape() {
  printf "%s" "$1" | sed "s/'/''/g"
}

print_query() {
  local title="$1"
  local query="$2"
  log "${title}"
  sqlite3 -header -column "${DB_PATH}" "${query}" || true
}

table_exists() {
  local table_name="$1"
  [[ "$(sql_value "SELECT name FROM sqlite_master WHERE type='table' AND name='${table_name}';")" == "${table_name}" ]]
}

required_tables_ready() {
  table_exists "User" && table_exists "SystemConfig" && table_exists "EdgeDevice"
}

seed_counts_ready() {
  local admin_count system_count edge_count
  local safe_edge_device_id
  safe_edge_device_id="$(sql_escape "${EDGE_DEVICE_ID}")"
  admin_count="$(sql_value "SELECT COUNT(*) FROM \"User\" WHERE username='admin' AND role='admin' AND isEnabled=1;")"
  system_count="$(sql_value "SELECT COUNT(*) FROM \"SystemConfig\" WHERE id='system';")"
  edge_count="$(sql_value "SELECT COUNT(*) FROM \"EdgeDevice\" WHERE deviceId='${safe_edge_device_id}' AND isEnabled=1;")"

  [[ "${admin_count}" == "1" && "${system_count}" == "1" && "${edge_count}" == "1" ]]
}

run_prisma_repair() {
  log "attempting database repair with prisma migrate deploy and seed"
  cd "${BACKEND_ROOT}"
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
  npx prisma migrate deploy
  npx prisma db seed
  fix_data_permissions
}

fix_data_permissions() {
  if id -u "${SERVICE_USER}" >/dev/null 2>&1; then
    ${SUDO} mkdir -p "${DATA_ROOT}"
    ${SUDO} chown -R "${SERVICE_USER}:${SERVICE_USER}" "${DATA_ROOT}"
  fi
}

ensure_database_state() {
  if [[ ! -f "${DB_PATH}" ]]; then
    log "database file ${DB_PATH} does not exist"
    run_prisma_repair
  fi

  if ! required_tables_ready; then
    log "one or more required tables are missing"
    run_prisma_repair
  fi

  required_tables_ready || fail "required tables missing after repair; expected User, SystemConfig, EdgeDevice"

  if ! seed_counts_ready; then
    log "one or more required seed rows are missing; running seed"
    cd "${BACKEND_ROOT}"
    set -a
    # shellcheck disable=SC1090
    source "${ENV_FILE}"
    set +a
    npx prisma db seed
    fix_data_permissions
  fi

  seed_counts_ready || fail "required seed rows missing after repair; expected admin, system, ${EDGE_DEVICE_ID}"
}

ensure_service_active() {
  if systemctl is-active --quiet "${SERVICE_NAME}"; then
    log "service ${SERVICE_NAME}: active"
    return
  fi

  log "service ${SERVICE_NAME} is not active; attempting restart"
  ${SUDO} systemctl restart "${SERVICE_NAME}" || true

  if ! systemctl is-active --quiet "${SERVICE_NAME}"; then
    ${SUDO} systemctl status "${SERVICE_NAME}" --no-pager || true
    fail "service ${SERVICE_NAME} is not active after restart"
  fi

  log "service ${SERVICE_NAME}: active after restart"
}

load_runtime_env
resolve_sqlite_path
ensure_tools
ensure_database_state
ensure_service_active

log "sqlite tables"
sqlite3 "${DB_PATH}" ".tables"

print_query "users" "SELECT username, role, isEnabled FROM \"User\";"
print_query "system config" "SELECT id, registrationEnabled, appEnabled FROM \"SystemConfig\";"
print_query "edge devices" "SELECT deviceId, isEnabled FROM \"EdgeDevice\";"

log "verification summary: service=ok tables=ok admin=ok system=ok edge_device=${EDGE_DEVICE_ID}=ok"
