#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="${SCRIPT_DIR}/.runtime"
PID_FILE="${RUNTIME_DIR}/pc-camera-worker.pid"
LOG_FILE="${RUNTIME_DIR}/pc-camera-worker.log"

if [ ! -f "${PID_FILE}" ]; then
  echo "pc-camera-worker is not running"
  echo "log=${LOG_FILE}"
  exit 0
fi

worker_pid="$(cat "${PID_FILE}")"

if [ -n "${worker_pid}" ] && kill -0 "${worker_pid}" 2>/dev/null; then
  echo "pc-camera-worker is running, PID=${worker_pid}"
  echo "log=${LOG_FILE}"
else
  echo "pc-camera-worker PID file exists but process is not running"
  echo "log=${LOG_FILE}"
  exit 1
fi
