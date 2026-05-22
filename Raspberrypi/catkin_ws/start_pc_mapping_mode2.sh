#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -f "${SCRIPT_DIR}/use_cleanscout_pc.sh" ]; then
  echo "Missing environment script: ${SCRIPT_DIR}/use_cleanscout_pc.sh" >&2
  exit 1
fi

source "${SCRIPT_DIR}/use_cleanscout_pc.sh"

START_RVIZ="${START_RVIZ:-1}"
SCAN_TOPIC="${SCAN_TOPIC:-/scan}"
IMU_TOPIC="${IMU_TOPIC:-/imu/data}"
VEL_TOPIC="${VEL_TOPIC:-/rf1/vel}"
ODOM_TOPIC="${ODOM_TOPIC:-/odom}"
MAP_ODOM_FRAME="${MAP_ODOM_FRAME:-odom}"

wait_for_topic() {
  local topic="$1"
  echo "Waiting for ${topic} ..."
  until rostopic list 2>/dev/null | grep -Fx -- "${topic}" >/dev/null; do
    sleep 1
  done
}

cleanup() {
  local status=$?
  trap - EXIT INT TERM
  if [ -n "${ODOM_PID:-}" ] && kill -0 "${ODOM_PID}" 2>/dev/null; then
    kill "${ODOM_PID}" 2>/dev/null || true
    wait "${ODOM_PID}" 2>/dev/null || true
  fi
  if [ -n "${MAP_PID:-}" ] && kill -0 "${MAP_PID}" 2>/dev/null; then
    kill "${MAP_PID}" 2>/dev/null || true
    wait "${MAP_PID}" 2>/dev/null || true
  fi
  if [ -n "${RVIZ_PID:-}" ] && kill -0 "${RVIZ_PID}" 2>/dev/null; then
    kill "${RVIZ_PID}" 2>/dev/null || true
    wait "${RVIZ_PID}" 2>/dev/null || true
  fi
  exit "${status}"
}

trap cleanup EXIT INT TERM

wait_for_topic "${SCAN_TOPIC}"
wait_for_topic "${IMU_TOPIC}"
wait_for_topic "${VEL_TOPIC}"

rosrun csrpi_base_bridge rf1_vel_to_odom.py \
  _k_m:=0.129675 \
  _odom_frame:="${MAP_ODOM_FRAME}" \
  _base_frame:=base_link \
  _publish_tf:=true \
  _publish_rate_hz:=30 &
ODOM_PID=$!

wait_for_topic "${ODOM_TOPIC}"

roslaunch clbrobot slam_406_lsm.launch \
  start_lsm:=false \
  scan_topic:="${SCAN_TOPIC}" \
  odom_frame:="${MAP_ODOM_FRAME}" \
  base_frame:=base_link &
MAP_PID=$!

wait_for_topic "/map"

if [ "${START_RVIZ}" = "1" ]; then
  rviz &
  RVIZ_PID=$!
else
  echo "RViz not started automatically. Launch it manually if needed."
fi

wait "${ODOM_PID}" "${MAP_PID}"
