#!/usr/bin/env bash
# set -e

# ===== CleanScout PC ROS network config =====
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

get_pc_ip() {
  ip route get 1.1.1.1 2>/dev/null | awk '{for (i = 1; i <= NF; ++i) if ($i == "src") { print $(i + 1); exit }}'
}

PC_IP="$(get_pc_ip)"

if [ -z "${PC_IP}" ]; then
  echo "Failed to detect local IPv4 address" >&2
  return 1 2>/dev/null || exit 1
fi

IFS='.' read -r o1 o2 o3 o4 <<< "${PC_IP}"

if [ -z "${o1}" ] || [ -z "${o2}" ] || [ -z "${o3}" ] || [ -z "${o4}" ]; then
  echo "Detected IPv4 address is invalid: ${PC_IP}" >&2
  return 1 2>/dev/null || exit 1
fi

PI_IP="${o1}.${o2}.${o3}.84"

source /opt/ros/noetic/setup.bash

if [ -f "${SCRIPT_DIR}/devel/setup.bash" ]; then
  source "${SCRIPT_DIR}/devel/setup.bash"
fi

export ROS_MASTER_URI="http://${PI_IP}:11311"
export ROS_IP="${PC_IP}"
unset ROS_HOSTNAME
unset ROS_IPV6

export CLBBASE="mecanum"
export CLBLIDAR="rplidar"

echo "CleanScout PC environment loaded"
echo "ROS_MASTER_URI=${ROS_MASTER_URI}"
echo "ROS_IP=${ROS_IP}"
