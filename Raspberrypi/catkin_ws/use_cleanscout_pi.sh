#!/usr/bin/env bash
set -e

# ===== CleanScout Pi ROS network config =====
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

get_pi_ip() {
  ip route get 1.1.1.1 2>/dev/null | awk '{for (i = 1; i <= NF; ++i) if ($i == "src") { print $(i + 1); exit }}'
}

PI_IP="$(get_pi_ip)"

if [ -z "${PI_IP}" ]; then
  echo "Failed to detect Raspberry Pi local IPv4 address" >&2
  return 1 2>/dev/null || exit 1
fi

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
