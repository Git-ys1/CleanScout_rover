#!/usr/bin/env bash
# set -e

# ===== CleanScout PC ROS network config =====
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "${SCRIPT_DIR}/cleanscout_network.sh"

PC_IP="$(cleanscout_current_ipv4)"

if [ -z "${PC_IP}" ]; then
  echo "Failed to detect local IPv4 address" >&2
  return 1 2>/dev/null || exit 1
fi

if ! PI_HOST="$(cleanscout_pi_host "${PC_IP}")"; then
  echo "Failed to resolve Raspberry Pi host for ${CLEANSCOUT_NETWORK_MODE}" >&2
  return 1 2>/dev/null || exit 1
fi

source /opt/ros/noetic/setup.bash

if [ -f "${SCRIPT_DIR}/devel/setup.bash" ]; then
  source "${SCRIPT_DIR}/devel/setup.bash"
fi

export ROS_MASTER_URI="http://${PI_HOST}:11311"
export ROS_IP="${PC_IP}"
unset ROS_HOSTNAME
unset ROS_IPV6

export CLBBASE="mecanum"
export CLBLIDAR="rplidar"

echo "CleanScout PC environment loaded"
echo "CLEANSCOUT_NETWORK_MODE=${CLEANSCOUT_NETWORK_MODE}"
echo "CLEANSCOUT_PI_HOST=${PI_HOST}"
echo "ROS_MASTER_URI=${ROS_MASTER_URI}"
echo "ROS_IP=${ROS_IP}"
