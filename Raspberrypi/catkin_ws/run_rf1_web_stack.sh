#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws"
LOG_FILE="/tmp/c322_rf1_web_stack.log"

source "$ROOT/use_cleanscout_pi.sh"

if [ -f "/home/clbrobot/catkin_ws/devel/setup.bash" ]; then
  source "/home/clbrobot/catkin_ws/devel/setup.bash"
fi

export ROS_PACKAGE_PATH="$ROOT/src:/home/clbrobot/catkin_ws/src:/opt/ros/noetic/share"

"$ROOT/clean_rf1_web_sessions.sh"

nohup bash -lc 'source "/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/use_cleanscout_pi.sh" && if [ -f "/home/clbrobot/catkin_ws/devel/setup.bash" ]; then source "/home/clbrobot/catkin_ws/devel/setup.bash"; fi && export ROS_PACKAGE_PATH="/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src:/home/clbrobot/catkin_ws/src:/opt/ros/noetic/share" && roslaunch "/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/src/clbrobot_project/clbrobot/launch/bringup_rf1_web.launch"' >"$LOG_FILE" 2>&1 </dev/null &

sleep 8

printf '\n[rf1-web] log file\n%s\n' "$LOG_FILE"

printf '\n[rf1-web] rostopic list\n'
rostopic list || true

printf '\n[rf1-web] rosbridge port\n'
ss -ltnp | grep ':9090' || true

printf '\n[rf1-web] stack launched\n'
