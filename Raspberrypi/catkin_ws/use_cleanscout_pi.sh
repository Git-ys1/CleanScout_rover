#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws"
IP="$(hostname -I | awk '{print $1}')"

source /opt/ros/noetic/setup.bash
source "$ROOT/devel/setup.bash"

export ROS_IP="$IP"
export ROS_HOSTNAME="$IP"
export ROS_MASTER_URI="http://$IP:11311"
export CLBBASE="mecanum"
export CLBLIDAR="rplidar"

echo "CleanScout Pi environment loaded"
echo "ROS_MASTER_URI=$ROS_MASTER_URI"
echo "ROS_IP=$ROS_IP"
echo "ROS_HOSTNAME=$ROS_HOSTNAME"
