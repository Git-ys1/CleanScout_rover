#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="${SCRIPT_DIR}/.runtime/pc-camera-worker.pid"

if [ ! -f "${PID_FILE}" ]; then
  echo "pc-camera-worker PID file not found"
  exit 0
fi

worker_pid="$(cat "${PID_FILE}")"

if [ -n "${worker_pid}" ] && kill -0 "${worker_pid}" 2>/dev/null; then
  kill "${worker_pid}"
  echo "pc-camera-worker stopped, PID=${worker_pid}"
else
  echo "pc-camera-worker is not running"
fi

rm -f "${PID_FILE}"
