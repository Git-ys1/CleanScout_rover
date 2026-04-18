#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws"

source "$ROOT/use_cleanscout_pi.sh"

"$ROOT/clean_ros_sessions.sh"

echo "[start] launching base stack in foreground shell"
nohup bash -lc 'source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh; roslaunch /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/nav_base_stack.launch' >/tmp/c236_nav_base.log 2>&1 </dev/null &

echo "[wait] waiting for base readiness: /scan /odom /csr_base/ack"
for i in $(seq 1 30); do
  scan_ok=0
  odom_ok=0
  ack_ok=0
  rostopic list 2>/dev/null | grep -q '^/scan$' && scan_ok=1 || true
  rostopic list 2>/dev/null | grep -q '^/odom$' && odom_ok=1 || true
  rostopic list 2>/dev/null | grep -q '^/csr_base/ack$' && ack_ok=1 || true
  echo "[wait] step=$i scan=$scan_ok odom=$odom_ok ack=$ack_ok"
  if [ "$scan_ok" -eq 1 ] && [ "$odom_ok" -eq 1 ] && [ "$ack_ok" -eq 1 ]; then
    break
  fi
  sleep 1
done

echo "[start] launching navigation layer in foreground"
roslaunch "$ROOT/src/clbrobot_project/clbrobot/launch/desk_map_navigation.launch"
