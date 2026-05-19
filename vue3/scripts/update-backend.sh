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
SERVICE_NAME="${SERVICE_NAME:-vline-backend}"
ENV_FILE="${ENV_FILE:-/etc/vline-backend.env}"
DEPLOY_REVISION="$(git -C "${REPO_ROOT}" rev-parse --short=12 HEAD 2>/dev/null || echo unknown)"
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

${SUDO} mkdir -p "${APP_ROOT}"
sync_backend_tree
printf '%s\n' "${DEPLOY_REVISION}" | ${SUDO} tee "${BACKEND_ROOT}/.deploy-revision" >/dev/null

cd "${BACKEND_ROOT}"
npm ci

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Environment file ${ENV_FILE} was not found. Create it before running Prisma commands." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL is missing after loading ${ENV_FILE}." >&2
  exit 1
fi

npx prisma generate
npx prisma migrate deploy
${SUDO} systemctl restart "${SERVICE_NAME}"

echo "Backend update finished."
echo "Backend directory: ${BACKEND_ROOT}"
echo "systemd service: ${SERVICE_NAME}"
echo "Environment file: ${ENV_FILE}"
echo "Deployed revision: ${DEPLOY_REVISION}"
