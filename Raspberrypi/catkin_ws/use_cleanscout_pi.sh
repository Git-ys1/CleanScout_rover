#!/usr/bin/env bash
set -e

# ===== CleanScout Pi ROS network config =====
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PI_IP="10.140.112.84"

source /opt/ros/noetic/setup.bash

if [ -f "${SCRIPT_DIR}/devel/setup.bash" ]; then
  source "${SCRIPT_DIR}/devel/setup.bash"
fi

export ROS_MASTER_URI="http://${PI_IP}:11311"
export ROS_IP="${PI_IP}"
unset ROS_HOSTNAME
unset ROS_IPV6

export CLBBASE="mecanum"
export CLBLIDAR="rplidar"

echo "CleanScout Pi environment loaded"
echo "ROS_MASTER_URI=${ROS_MASTER_URI}"
echo "ROS_IP=${ROS_IP}"
