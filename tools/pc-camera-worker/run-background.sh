#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="${SCRIPT_DIR}/.runtime"
PID_FILE="${RUNTIME_DIR}/pc-camera-worker.pid"
LOG_FILE="${RUNTIME_DIR}/pc-camera-worker.log"

mkdir -p "${RUNTIME_DIR}"

if [ ! -f "${SCRIPT_DIR}/.env" ]; then
  echo "Missing ${SCRIPT_DIR}/.env. Copy .env.local or .env.example first." >&2
  exit 1
fi

if [ -f "${PID_FILE}" ]; then
  existing_pid="$(cat "${PID_FILE}")"
  if [ -n "${existing_pid}" ] && kill -0 "${existing_pid}" 2>/dev/null; then
    echo "pc-camera-worker is already running with PID ${existing_pid}"
    exit 0
  fi
fi

nohup node "${SCRIPT_DIR}/src/index.js" >>"${LOG_FILE}" 2>&1 &
worker_pid=$!
echo "${worker_pid}" > "${PID_FILE}"

sleep 1

if kill -0 "${worker_pid}" 2>/dev/null; then
  echo "pc-camera-worker started in background, PID=${worker_pid}"
  echo "log=${LOG_FILE}"
else
  echo "pc-camera-worker failed to stay running; check ${LOG_FILE}" >&2
  exit 1
fi
