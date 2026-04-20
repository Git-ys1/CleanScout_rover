#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws"
LIDAR_LOG="/tmp/c330_nav_lidar.log"
NAV_LOG="/tmp/c330_nav_406.log"

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

require_package() {
  local pkg="$1"
  if ! rospack find "$pkg" >/dev/null 2>&1; then
    echo "[c330-nav] ERROR: 缺少 ROS 包 $pkg"
    return 1
  fi
  return 0
}

echo "[c330-nav] source 环境"
source "$ROOT/use_cleanscout_pi.sh"

echo "[c330-nav] 检查导航依赖"
for pkg in map_server amcl move_base; do
  if ! require_package "$pkg"; then
    echo "[c330-nav] 当前机器导航链依赖不完整"
    exit 1
  fi
done

echo "[c330-nav] 提示：当前 RPLIDAR 运行时仍依赖旧 ~/catkin_ws 已编译 rplidarNode"

echo "[c330-nav] 清理旧会话"
"$ROOT/clean_mapping_nav_sessions.sh"

echo "[c330-nav] 执行 run_rf1_core_stack.sh"
"$ROOT/run_rf1_core_stack.sh"

echo "[c330-nav] 单独启动 RPLIDAR"
nohup bash -lc 'source "/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh" && roslaunch "/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/lidar/rplidar.launch"' >"$LIDAR_LOG" 2>&1 </dev/null &

echo "[c330-nav] 等待 /scan 5s 内就绪"
if ! wait_for_topic /scan 5; then
  echo "[c330-nav] ERROR: /scan 未就绪"
  exit 1
fi

echo "[c330-nav] 单独启动 nav_406.launch"
nohup bash -lc 'source "/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh" && roslaunch "/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/nav/nav_406.launch"' >"$NAV_LOG" 2>&1 </dev/null &

echo "[c330-nav] 等待 /amcl_pose 3s 内就绪"
if ! wait_for_topic /amcl_pose 3; then
  echo "[c330-nav] ERROR: /amcl_pose 未就绪"
  exit 1
fi

echo "[c330-nav] 等待 /move_base/status 3s 内就绪"
if ! wait_for_topic /move_base/status 3; then
  echo "[c330-nav] ERROR: /move_base/status 未就绪"
  exit 1
fi

echo "[c330-nav] 406 导航链已就绪"
