#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws"
LOG_FILE="/tmp/c324_edge_relay.log"

source "$ROOT/use_cleanscout_pi.sh"

export EDGE_RELAY_ENABLED="${EDGE_RELAY_ENABLED:-false}"
export EDGE_RELAY_URL="${EDGE_RELAY_URL:-wss://api.hzhhds.top/edge/ros}"
export EDGE_DEVICE_ID="${EDGE_DEVICE_ID:-csrpi-001}"
export EDGE_DEVICE_TOKEN="${EDGE_DEVICE_TOKEN:-}"
export EDGE_HEARTBEAT_MS="${EDGE_HEARTBEAT_MS:-5000}"
export EDGE_ODOM_HZ="${EDGE_ODOM_HZ:-5}"
export EDGE_IMU_HZ="${EDGE_IMU_HZ:-5}"
export EDGE_SCAN_HZ="${EDGE_SCAN_HZ:-1}"
export EDGE_CMD_REPEAT_HZ="${EDGE_CMD_REPEAT_HZ:-10}"
export EDGE_CMD_DEFAULT_HOLD_MS="${EDGE_CMD_DEFAULT_HOLD_MS:-400}"
export EDGE_RECONNECT_DELAY_MS="${EDGE_RECONNECT_DELAY_MS:-1000}"

"$ROOT/clean_edge_relay_sessions.sh"

nohup bash -lc 'source "/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh" && export ROS_PACKAGE_PATH="/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src:/opt/ros/noetic/share" && roslaunch "/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/csrpi_edge_relay/launch/edge_relay.launch" enabled:="$EDGE_RELAY_ENABLED" url:="$EDGE_RELAY_URL" device_id:="$EDGE_DEVICE_ID" device_token:="$EDGE_DEVICE_TOKEN" heartbeat_ms:="$EDGE_HEARTBEAT_MS" odom_hz:="$EDGE_ODOM_HZ" imu_hz:="$EDGE_IMU_HZ" scan_hz:="$EDGE_SCAN_HZ" cmd_repeat_hz:="$EDGE_CMD_REPEAT_HZ" default_hold_ms:="$EDGE_CMD_DEFAULT_HOLD_MS" reconnect_delay_ms:="$EDGE_RECONNECT_DELAY_MS"' >"$LOG_FILE" 2>&1 </dev/null &

sleep 6

printf '[edge-relay] log file\n%s\n' "$LOG_FILE"
