#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws"
LIDAR_LOG="/tmp/c330_lidar.log"
SLAM_LOG="/tmp/c330_slam_406.log"

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
    echo "[c330-mapping] ERROR: 缺少 ROS 包 $pkg"
    return 1
  fi
  return 0
}

echo "[c330-mapping] source 环境"
source "$ROOT/use_cleanscout_pi.sh"

echo "[c330-mapping] 检查 gmapping 依赖"
if ! require_package gmapping; then
  echo "[c330-mapping] 当前机器没有 gmapping，406 建图链暂时无法完整启动"
  echo "[c330-mapping] 注意：旧链实际使用的是 pkg=gmapping type=slam_gmapping"
  exit 1
fi

echo "[c330-mapping] 提示：当前 RPLIDAR 运行时仍依赖旧 ~/catkin_ws 已编译 rplidarNode"

echo "[c330-mapping] 执行 run_rf1_core_stack.sh"
"$ROOT/run_rf1_core_stack.sh"

echo "[c330-mapping] 单独启动 RPLIDAR"
nohup bash -lc 'source "/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh" && roslaunch "/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/lidar/rplidar.launch"' >"$LIDAR_LOG" 2>&1 </dev/null &

echo "[c330-mapping] 等待 /scan 5s 内就绪"
if ! wait_for_topic /scan 5; then
  echo "[c330-mapping] ERROR: /scan 未就绪"
  exit 1
fi

echo "[c330-mapping] 单独启动 slam_406.launch"
nohup bash -lc 'source "/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh" && roslaunch "/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/slam/slam_406.launch"' >"$SLAM_LOG" 2>&1 </dev/null &

echo "[c330-mapping] 等待 /map 3s 内就绪"
if ! wait_for_topic /map 3; then
  echo "[c330-mapping] ERROR: /map 未就绪"
  exit 1
fi

echo "[c330-mapping] 406 建图链已就绪"
echo "[c330-mapping] 现在到上位机 / 虚拟机 RViz 开始建图"
echo "[c330-mapping] 保存地图请运行 save_map_406.sh"
