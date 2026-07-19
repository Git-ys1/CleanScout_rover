#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws"
CORE_LOG="/tmp/c330_rf1_core.log"

cleanup_on_error() {
  local code=$?
  if [ "$code" -ne 0 ]; then
    echo "[c330-core] ERROR: 启动失败，自动清理残留 ROS 会话"
    bash "$ROOT/clean_mapping_nav_sessions.sh" || true
  fi
  exit "$code"
}

trap cleanup_on_error EXIT

wait_for_topic() {
  local topic="$1"
  local timeout_sec="$2"
  local step="0.2"
  local elapsed="0"
  while (( $(awk "BEGIN {print ($elapsed < $timeout_sec)}") )); do
    if rostopic list 2>/dev/null | grep -qx "$topic"; then
      return 0
    fi
    sleep "$step"
    elapsed=$(awk "BEGIN {print $elapsed + $step}")
  done
  return 1
}

wait_for_master() {
  local timeout_sec="$1"
  local step="0.2"
  local elapsed="0"
  while (( $(awk "BEGIN {print ($elapsed < $timeout_sec)}") )); do
    if rosparam get /run_id >/dev/null 2>&1; then
      return 0
    fi
    sleep "$step"
    elapsed=$(awk "BEGIN {print $elapsed + $step}")
  done
  return 1
}

echo "[c330-core] source 环境"
source "$ROOT/use_cleanscout_pi.sh"

echo "[c330-core] 清理旧会话"
bash "$ROOT/clean_mapping_nav_sessions.sh"

echo "[c330-core] 显式启动 roscore"
nohup bash -lc 'source "/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh" && roscore' >/tmp/c330_roscore.log 2>&1 </dev/null &

echo "[c330-core] 等待 roscore 就绪"
if ! wait_for_master 10; then
  echo "[c330-core] ERROR: roscore 未在 10s 内就绪，请检查 /tmp/c330_roscore.log"
  exit 1
fi

echo "[c330-core] 启动 RF1 core"
nohup bash -lc 'source "/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh" && roslaunch "/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/core/bringup_rf1_core.launch"' >"$CORE_LOG" 2>&1 </dev/null &

echo "[c330-core] 等待 /rf1/vel 就绪"
if ! wait_for_topic /rf1/vel 10; then
  echo "[c330-core] ERROR: /rf1/vel 未在 10s 内就绪"
  exit 1
fi

echo "[c330-core] RF1 core 已就绪"
trap - EXIT
