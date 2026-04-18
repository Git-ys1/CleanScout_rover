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

sync_backend_tree() {
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
    "${source_unit}" > "${temp_unit}"

  ${SUDO} install -m 644 "${temp_unit}" "${SYSTEMD_UNIT_PATH}"
  rm -f "${temp_unit}"
}

${SUDO} mkdir -p "${APP_ROOT}" "${DATA_ROOT}"
sync_backend_tree

cd "${BACKEND_ROOT}"
npm ci
npx prisma generate
npx prisma migrate deploy

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Environment file ${ENV_FILE} was not found. Create it first and point DATABASE_URL to a path outside the repo, for example ${DATA_ROOT}/dev.db" >&2
  exit 1
fi

render_systemd_unit
${SUDO} systemctl daemon-reload
${SUDO} systemctl enable "${SERVICE_NAME}"
${SUDO} systemctl restart "${SERVICE_NAME}"

echo "Backend initial deployment finished."
echo "Backend directory: ${BACKEND_ROOT}"
echo "systemd service: ${SERVICE_NAME}"
echo "Environment file: ${ENV_FILE}"
