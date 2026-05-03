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
SYSTEMD_UNIT_PATH="${SYSTEMD_UNIT_PATH:-/etc/systemd/system/${SERVICE_NAME}.service}"
SUDO=''

if [[ "${EUID}" -ne 0 ]]; then
  SUDO='sudo'
fi

log() {
  echo "[bootstrap-backend] $*"
}

fail() {
  echo "[bootstrap-backend] ERROR: $*" >&2
  exit 1
}

dedupe_packages() {
  local item
  printf '%s\n' "$@" | awk 'NF && !seen[$0]++ { print }'
}

install_missing_dependencies() {
  local missing=()
  local packages=()
  local command_name

  for command_name in node npm npx rsync sqlite3 systemctl; do
    if ! command -v "${command_name}" >/dev/null 2>&1; then
      missing+=("${command_name}")
    fi
  done

  if [[ "${#missing[@]}" -eq 0 ]]; then
    log "dependency check passed"
    return
  fi

  if ! command -v apt-get >/dev/null 2>&1; then
    fail "missing commands: ${missing[*]}; automatic install only supports Ubuntu/Debian with apt-get"
  fi

  for command_name in "${missing[@]}"; do
    case "${command_name}" in
      node)
        packages+=("nodejs")
        ;;
      npm | npx)
        packages+=("npm")
        ;;
      rsync)
        packages+=("rsync")
        ;;
      sqlite3)
        packages+=("sqlite3")
        ;;
      systemctl)
        packages+=("systemd")
        ;;
    esac
  done

  mapfile -t packages < <(dedupe_packages "${packages[@]}")
  log "installing missing dependencies: ${packages[*]}"
  ${SUDO} apt-get update
  ${SUDO} DEBIAN_FRONTEND=noninteractive apt-get install -y "${packages[@]}"

  for command_name in node npm npx rsync sqlite3 systemctl; do
    command -v "${command_name}" >/dev/null 2>&1 || fail "dependency ${command_name} is still missing after apt install"
  done
}

check_node_version() {
  local major
  major="$(node -p "Number(process.versions.node.split('.')[0])" 2>/dev/null || echo 0)"

  if [[ "${major}" -lt 18 ]]; then
    fail "Node.js 18+ is required, current version is $(node -v 2>/dev/null || echo unknown). Install Node 22/24 LTS and rerun bootstrap."
  fi

  log "node version check passed: $(node -v)"
}

load_runtime_env() {
  [[ -f "${ENV_FILE}" ]] || fail "environment file ${ENV_FILE} was not found"

  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a

  [[ -n "${DATABASE_URL:-}" ]] || fail "DATABASE_URL is required in ${ENV_FILE}"
  [[ -n "${JWT_SECRET:-}" ]] || fail "JWT_SECRET is required in ${ENV_FILE}"
  [[ -n "${EDGE_DEVICE_BOOTSTRAP_ID:-}" ]] || fail "EDGE_DEVICE_BOOTSTRAP_ID is required in ${ENV_FILE}"
  [[ -n "${EDGE_DEVICE_BOOTSTRAP_TOKEN:-}" ]] || fail "EDGE_DEVICE_BOOTSTRAP_TOKEN is required in ${ENV_FILE}"
}

ensure_service_user() {
  if id -u "${SERVICE_USER}" >/dev/null 2>&1; then
    log "service user exists: ${SERVICE_USER}"
    return
  fi

  log "creating system service user: ${SERVICE_USER}"
  ${SUDO} useradd --system --home-dir /nonexistent --shell /usr/sbin/nologin "${SERVICE_USER}"
}

fix_data_permissions() {
  if id -u "${SERVICE_USER}" >/dev/null 2>&1; then
    ${SUDO} mkdir -p "${DATA_ROOT}"
    ${SUDO} chown -R "${SERVICE_USER}:${SERVICE_USER}" "${DATA_ROOT}"
  fi
}

sync_backend_tree() {
  ${SUDO} mkdir -p "${APP_ROOT}" "${BACKEND_ROOT}" "${DATA_ROOT}"

  if command -v rsync >/dev/null 2>&1; then
    ${SUDO} rsync -a --delete "${REPO_ROOT}/backend/" "${BACKEND_ROOT}/"
    return
  fi

  ${SUDO} rm -rf "${BACKEND_ROOT}"
  ${SUDO} mkdir -p "${BACKEND_ROOT}"
  ${SUDO} cp -a "${REPO_ROOT}/backend/." "${BACKEND_ROOT}/"
}

render_systemd_unit() {
  local source_unit="${REPO_ROOT}/deploy/systemd/vline-backend.service"
  local temp_unit
  temp_unit="$(mktemp)"

  sed \
    -e "s|^User=.*$|User=${SERVICE_USER}|" \
    -e "s|^WorkingDirectory=.*$|WorkingDirectory=${BACKEND_ROOT}|" \
    -e "s|^EnvironmentFile=.*$|EnvironmentFile=${ENV_FILE}|" \
    -e "s|^Environment=ENV_FILE=.*$|Environment=ENV_FILE=${ENV_FILE}|" \
    "${source_unit}" > "${temp_unit}"

  ${SUDO} install -m 644 "${temp_unit}" "${SYSTEMD_UNIT_PATH}"
  rm -f "${temp_unit}"
}

install_missing_dependencies
check_node_version
load_runtime_env
ensure_service_user
sync_backend_tree

cd "${BACKEND_ROOT}"
log "installing backend dependencies"
npm ci

log "running prisma generate / migrate / seed"
npx prisma generate
npx prisma migrate deploy
npx prisma db seed
fix_data_permissions

log "installing systemd service"
render_systemd_unit
${SUDO} systemctl daemon-reload
${SUDO} systemctl enable "${SERVICE_NAME}"
${SUDO} systemctl restart "${SERVICE_NAME}"

log "running post-deploy verification"
ENV_FILE="${ENV_FILE}" \
APP_ROOT="${APP_ROOT}" \
BACKEND_ROOT="${BACKEND_ROOT}" \
DATA_ROOT="${DATA_ROOT}" \
SERVICE_NAME="${SERVICE_NAME}" \
SERVICE_USER="${SERVICE_USER}" \
bash "${REPO_ROOT}/scripts/check-backend-state.sh"

log "initial backend bootstrap finished"
log "backend directory: ${BACKEND_ROOT}"
log "systemd service: ${SERVICE_NAME}"
log "environment file: ${ENV_FILE}"
