#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EDGE_URL="wss://api.hzhhds.top/edge/ros"

source "${SCRIPT_DIR}/cleanscout_network.sh"

CURRENT_IP="$(cleanscout_current_ipv4)"
EDGE_FALLBACK_HOST_SUFFIX="${EDGE_FALLBACK_HOST_SUFFIX:-190}"
EDGE_FALLBACK_HOST="${EDGE_FALLBACK_HOST:-$(cleanscout_pc_host "${CURRENT_IP}" "${EDGE_FALLBACK_HOST_SUFFIX}")}"
EDGE_FALLBACK_URL="${EDGE_FALLBACK_URL:-ws://${EDGE_FALLBACK_HOST}:3000/edge/ros}"
EDGE_PRIMARY_FAILURES_BEFORE_FALLBACK="3"
EDGE_DEVICE_ID="${EDGE_DEVICE_ID:-csrpi-001}"
EDGE_DEVICE_TOKEN="${EDGE_DEVICE_TOKEN:-}"
EDGE_CMD_TOPIC="${EDGE_CMD_TOPIC:-/cmd_vel_nav}"
EDGE_ODOM_TOPIC="${EDGE_ODOM_TOPIC:-/odom}"
EDGE_ALLOW_MANUAL_CONTROL="${EDGE_ALLOW_MANUAL_CONTROL:-true}"
EDGE_PUBLISH_CMD_VEL="${EDGE_PUBLISH_CMD_VEL:-true}"
EDGE_TOGGLE_MOTION_ENABLED="${EDGE_TOGGLE_MOTION_ENABLED:-true}"
EDGE_ALLOW_FAN_CONTROL="${EDGE_ALLOW_FAN_CONTROL:-true}"
# Command-side yaw gain. Keep it explicit because encoder odom on the PC uses
# a separately calibrated ODOM_K_M to reconstruct actual angular velocity.
RF1_CMD_K_M="${RF1_CMD_K_M:-0.1987}"
RF1_MIN_WHEEL_MS="${RF1_MIN_WHEEL_MS:-0.0}"

if [ -z "${EDGE_DEVICE_TOKEN}" ]; then
  echo "EDGE_DEVICE_TOKEN is required; inject it through the environment" >&2
  exit 1
fi

source "${SCRIPT_DIR}/use_cleanscout_pi.sh"

wait_for_master() {
  echo "Waiting for ROS master ..."
  until rosparam get /run_id >/dev/null 2>&1; do
    sleep 1
  done
}

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
  if [ -n "${RSP_PID:-}" ] && kill -0 "${RSP_PID}" 2>/dev/null; then
    kill "${RSP_PID}" 2>/dev/null || true
    wait "${RSP_PID}" 2>/dev/null || true
  fi
  if [ -n "${BRINGUP_PID:-}" ] && kill -0 "${BRINGUP_PID}" 2>/dev/null; then
    kill "${BRINGUP_PID}" 2>/dev/null || true
    wait "${BRINGUP_PID}" 2>/dev/null || true
  fi
  if [ -n "${LIDAR_PID:-}" ] && kill -0 "${LIDAR_PID}" 2>/dev/null; then
    kill "${LIDAR_PID}" 2>/dev/null || true
    wait "${LIDAR_PID}" 2>/dev/null || true
  fi
  if [ -n "${GATE_PID:-}" ] && kill -0 "${GATE_PID}" 2>/dev/null; then
    kill "${GATE_PID}" 2>/dev/null || true
    wait "${GATE_PID}" 2>/dev/null || true
  fi
  if [ -n "${FAN_PID:-}" ] && kill -0 "${FAN_PID}" 2>/dev/null; then
    kill "${FAN_PID}" 2>/dev/null || true
    wait "${FAN_PID}" 2>/dev/null || true
  fi
  if [ -n "${EDGE_PID:-}" ] && kill -0 "${EDGE_PID}" 2>/dev/null; then
    kill "${EDGE_PID}" 2>/dev/null || true
    wait "${EDGE_PID}" 2>/dev/null || true
  fi
  if [ -n "${ROSCORE_PID:-}" ] && kill -0 "${ROSCORE_PID}" 2>/dev/null; then
    kill "${ROSCORE_PID}" 2>/dev/null || true
    wait "${ROSCORE_PID}" 2>/dev/null || true
  fi
  exit "${status}"
}

trap cleanup EXIT INT TERM

bash "${SCRIPT_DIR}/clean_ros_sessions.sh" || true
bash "${SCRIPT_DIR}/clean_mapping_nav_sessions.sh"
bash "${SCRIPT_DIR}/clean_edge_relay_sessions.sh" || true

sleep 2

roscore &
ROSCORE_PID=$!
wait_for_master
sleep 1

roslaunch "${SCRIPT_DIR}/src/clbrobot_project/clbrobot/launch/robot_state_publisher.launch" &
RSP_PID=$!

echo "Starting RF1 command bridge with RF1_CMD_K_M=${RF1_CMD_K_M} RF1_MIN_WHEEL_MS=${RF1_MIN_WHEEL_MS}"
roslaunch "${SCRIPT_DIR}/src/clbrobot_project/clbrobot/launch/bringup_rf1_min.launch" \
  k_m:="${RF1_CMD_K_M}" \
  min_wheel_ms:="${RF1_MIN_WHEEL_MS}" &
BRINGUP_PID=$!
wait_for_topic "/rf1/vel"

roslaunch "${SCRIPT_DIR}/src/clbrobot_project/clbrobot/launch/lidar/rplidar.launch" publish_static_tf:=false &
LIDAR_PID=$!
wait_for_topic "/scan"

roslaunch "${SCRIPT_DIR}/src/csrpi_base_bridge/launch/cmd_vel_safety_gate.launch" &
GATE_PID=$!

roslaunch "${SCRIPT_DIR}/src/csrpi_fan_bridge/launch/fan_dual_lid_bridge.launch" &
FAN_PID=$!

roslaunch "${SCRIPT_DIR}/src/csrpi_edge_relay/launch/edge_relay.launch" \
  enabled:=true \
  url:="${EDGE_URL}" \
  fallback_url:="${EDGE_FALLBACK_URL}" \
  primary_failures_before_fallback:="${EDGE_PRIMARY_FAILURES_BEFORE_FALLBACK}" \
  device_id:="${EDGE_DEVICE_ID}" \
  device_token:="${EDGE_DEVICE_TOKEN}" \
  toggle_motion_enabled:="${EDGE_TOGGLE_MOTION_ENABLED}" \
  allow_manual_control:="${EDGE_ALLOW_MANUAL_CONTROL}" \
  publish_cmd_vel:="${EDGE_PUBLISH_CMD_VEL}" \
  cmd_vel_topic:="${EDGE_CMD_TOPIC}" \
  odom_topic:="${EDGE_ODOM_TOPIC}" \
  allow_fan_control:="${EDGE_ALLOW_FAN_CONTROL}" &
EDGE_PID=$!

wait "${BRINGUP_PID}" "${LIDAR_PID}" "${GATE_PID}" "${FAN_PID}" "${EDGE_PID}"
