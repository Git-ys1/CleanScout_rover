#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws"
IP="$(hostname -I | awk '{print $1}')"

source /opt/ros/noetic/setup.bash

if [ -f "$ROOT/devel/setup.bash" ]; then
  source "$ROOT/devel/setup.bash"
else
  export ROS_PACKAGE_PATH="$ROOT/src${ROS_PACKAGE_PATH:+:$ROS_PACKAGE_PATH}"
fi

export ROS_IP="$IP"
export ROS_HOSTNAME="$IP"
export ROS_MASTER_URI="http://$IP:11311"
export CLBBASE="mecanum"
export CLBLIDAR="rplidar"

echo "CleanScout Pi environment loaded"
echo "ROS_MASTER_URI=$ROS_MASTER_URI"
echo "ROS_IP=$ROS_IP"
echo "ROS_HOSTNAME=$ROS_HOSTNAME"
