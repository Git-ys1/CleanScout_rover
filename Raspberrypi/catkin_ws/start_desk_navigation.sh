#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws"
ROSCORE_LOG="/tmp/c331_nav_roscore.log"
RF1_LOG="/tmp/c331_nav_rf1.log"
IMU_LOG="/tmp/c331_nav_imu.log"
LIDAR_LOG="/tmp/c331_nav_lidar.log"
LSM_LOG="/tmp/c331_nav_lsm.log"
NAV_LOG="/tmp/c331_nav_406.log"

cleanup_on_error() {
  local code=$?
  if [ "$code" -ne 0 ]; then
    echo "[c331-nav] ERROR: 启动失败，自动清理残留 ROS 会话"
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
    if rosparam get /rosdistro >/dev/null 2>&1; then
      return 0
    fi
    sleep "$step"
    elapsed=$(awk "BEGIN {print $elapsed + $step}")
  done
  return 1
}

launch_bg() {
  local log_file="$1"
  shift

  nohup bash -lc "$*" >"$log_file" 2>&1 </dev/null &
  local pid=$!
  sleep 1

  if ! kill -0 "$pid" 2>/dev/null; then
    echo "[c331-nav] ERROR: 后台进程启动后立刻退出"
    echo "[c331-nav] ERROR: 请检查日志 $log_file"
    return 1
  fi

  printf '%s' "$pid"
}

source "$ROOT/use_cleanscout_pi.sh"

echo "[c331-nav] clean 旧会话"
bash "$ROOT/clean_mapping_nav_sessions.sh"

echo "[c331-nav] 显式启动 roscore"
ROSCORE_PID=$(launch_bg "$ROSCORE_LOG" 'source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh && roscore')

if ! wait_for_master 8; then
  echo "[c331-nav] ERROR: roscore 未在预期时间内就绪"
  echo "[c331-nav] ERROR: 请检查日志 $ROSCORE_LOG"
  exit 1
fi

echo "[c331-nav] 启动 bringup_rf1_min.launch"
RF1_PID=$(launch_bg "$RF1_LOG" 'source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh && roslaunch /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/bringup_rf1_min.launch')

echo "[c331-nav] 等待 /rf1/vel"
if ! wait_for_topic /rf1/vel 8; then
  echo "[c331-nav] ERROR: /rf1/vel 未就绪"
  if ! kill -0 "$RF1_PID" 2>/dev/null; then
    echo "[c331-nav] ERROR: bringup_rf1_min.launch 已退出，请检查 $RF1_LOG"
  fi
  exit 1
fi

echo "[c331-nav] 启动 imu_only.launch"
IMU_PID=$(launch_bg "$IMU_LOG" 'source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh && roslaunch /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/core/imu_only.launch')

echo "[c331-nav] 等待 /imu/data"
if ! wait_for_topic /imu/data 8; then
  echo "[c331-nav] ERROR: /imu/data 未就绪"
  if ! kill -0 "$IMU_PID" 2>/dev/null; then
    echo "[c331-nav] ERROR: imu_only.launch 已退出，请检查 $IMU_LOG"
  fi
  exit 1
fi

echo "[c331-nav] 启动 lidar/rplidar.launch"
LIDAR_PID=$(launch_bg "$LIDAR_LOG" 'source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh && roslaunch /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/lidar/rplidar.launch')

echo "[c331-nav] 等待 /scan"
if ! wait_for_topic /scan 8; then
  echo "[c331-nav] ERROR: /scan 未就绪"
  if ! kill -0 "$LIDAR_PID" 2>/dev/null; then
    echo "[c331-nav] ERROR: lidar/rplidar.launch 已退出，请检查 $LIDAR_LOG"
  fi
  exit 1
fi

echo "[c331-nav] 启动 laser_scan_matcher_406.launch"
LSM_PID=$(launch_bg "$LSM_LOG" 'source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh && roslaunch /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/slam/laser_scan_matcher_406.launch')

echo "[c331-nav] 等待 /odom_lsm"
if ! wait_for_topic /odom_lsm 8; then
  echo "[c331-nav] ERROR: /odom_lsm 未就绪"
  if ! kill -0 "$LSM_PID" 2>/dev/null; then
    echo "[c331-nav] ERROR: laser_scan_matcher_406.launch 已退出，请检查 $LSM_LOG"
  fi
  exit 1
fi

echo "[c331-nav] 启动 nav/navigation_406_rf1.launch"
NAV_PID=$(launch_bg "$NAV_LOG" 'source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh && roslaunch /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/nav/navigation_406_rf1.launch')

echo "[c331-nav] 等待 /odom_lsm"
if ! wait_for_topic /odom_lsm 3; then
  echo "[c331-nav] ERROR: /odom_lsm 未就绪"
  if ! kill -0 "$NAV_PID" 2>/dev/null; then
    echo "[c331-nav] ERROR: navigation_406_rf1.launch 已退出，请检查 $NAV_LOG"
  fi
  exit 1
fi

echo "[c331-nav] 等待 /amcl_pose"
if ! wait_for_topic /amcl_pose 3; then
  echo "[c331-nav] ERROR: /amcl_pose 未就绪"
  if ! kill -0 "$NAV_PID" 2>/dev/null; then
    echo "[c331-nav] ERROR: navigation_406_rf1.launch 已退出，请检查 $NAV_LOG"
  fi
  exit 1
fi

echo "[c331-nav] 等待 /move_base/status"
if ! wait_for_topic /move_base/status 3; then
  echo "[c331-nav] ERROR: /move_base/status 未就绪"
  if ! kill -0 "$NAV_PID" 2>/dev/null; then
    echo "[c331-nav] ERROR: navigation_406_rf1.launch 已退出，请检查 $NAV_LOG"
  fi
  exit 1
fi

echo "[c331-nav] 406 导航链已就绪"
trap - EXIT
