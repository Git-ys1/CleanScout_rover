#!/usr/bin/env bash

# CleanScout network baseline. This file is sourced by PC and Raspberry Pi
# entrypoints; running it directly prints the currently resolved topology.

case "${CLEANSCOUT_NETWORK_MODE:-portable_wifi}" in
  portable|portable_wifi|portable-wifi)
    CLEANSCOUT_NETWORK_MODE="portable_wifi"
    ;;
  phone|phone_hotspot|phone-hotspot)
    CLEANSCOUT_NETWORK_MODE="phone_hotspot"
    ;;
  *)
    printf 'Unsupported CLEANSCOUT_NETWORK_MODE: %s\n' "${CLEANSCOUT_NETWORK_MODE}" >&2
    return 2 2>/dev/null || exit 2
    ;;
esac

CLEANSCOUT_PORTABLE_SSID="${CLEANSCOUT_PORTABLE_SSID:-My Super Net}"
CLEANSCOUT_PORTABLE_SUBNET="${CLEANSCOUT_PORTABLE_SUBNET:-192.168.8}"
CLEANSCOUT_PORTABLE_GATEWAY="${CLEANSCOUT_PORTABLE_GATEWAY:-${CLEANSCOUT_PORTABLE_SUBNET}.1}"
CLEANSCOUT_PORTABLE_PI_IP="${CLEANSCOUT_PORTABLE_PI_IP:-${CLEANSCOUT_PORTABLE_SUBNET}.108}"
CLEANSCOUT_PORTABLE_ORANGEPI_IP="${CLEANSCOUT_PORTABLE_ORANGEPI_IP:-${CLEANSCOUT_PORTABLE_SUBNET}.148}"
CLEANSCOUT_PORTABLE_PC_IP="${CLEANSCOUT_PORTABLE_PC_IP:-${CLEANSCOUT_PORTABLE_SUBNET}.222}"
CLEANSCOUT_PHONE_PI_SUFFIX="${CLEANSCOUT_PHONE_PI_SUFFIX:-84}"
CLEANSCOUT_PHONE_PC_SUFFIX="${CLEANSCOUT_PHONE_PC_SUFFIX:-190}"

export CLEANSCOUT_NETWORK_MODE
export CLEANSCOUT_PORTABLE_SSID
export CLEANSCOUT_PORTABLE_SUBNET
export CLEANSCOUT_PORTABLE_GATEWAY
export CLEANSCOUT_PORTABLE_PI_IP
export CLEANSCOUT_PORTABLE_ORANGEPI_IP
export CLEANSCOUT_PORTABLE_PC_IP
export CLEANSCOUT_PHONE_PI_SUFFIX
export CLEANSCOUT_PHONE_PC_SUFFIX

cleanscout_current_ipv4() {
  ip route get 1.1.1.1 2>/dev/null |
    awk '{for (i = 1; i <= NF; ++i) if ($i == "src") { print $(i + 1); exit }}'
}

cleanscout_host_from_suffix() {
  local current_ip="$1"
  local suffix="$2"
  local o1 o2 o3 o4

  IFS='.' read -r o1 o2 o3 o4 <<< "${current_ip}"
  if [ -z "${o1}" ] || [ -z "${o2}" ] || [ -z "${o3}" ] || [ -z "${o4}" ]; then
    printf 'Cannot derive legacy hotspot host from IPv4: %s\n' "${current_ip}" >&2
    return 1
  fi

  printf '%s.%s.%s.%s' "${o1}" "${o2}" "${o3}" "${suffix}"
}

cleanscout_pi_host() {
  local current_ip="$1"
  local phone_suffix="${2:-${CLEANSCOUT_PHONE_PI_SUFFIX}}"

  if [ -n "${CLEANSCOUT_PI_HOST:-}" ]; then
    printf '%s' "${CLEANSCOUT_PI_HOST}"
    return 0
  fi

  case "${CLEANSCOUT_NETWORK_MODE}" in
    portable_wifi)
      printf '%s' "${CLEANSCOUT_PORTABLE_PI_IP}"
      ;;
    phone_hotspot)
      cleanscout_host_from_suffix "${current_ip}" "${phone_suffix}"
      ;;
  esac
}

cleanscout_pc_host() {
  local current_ip="$1"
  local phone_suffix="${2:-${CLEANSCOUT_PHONE_PC_SUFFIX}}"

  if [ -n "${CLEANSCOUT_PC_HOST:-}" ]; then
    printf '%s' "${CLEANSCOUT_PC_HOST}"
    return 0
  fi

  case "${CLEANSCOUT_NETWORK_MODE}" in
    portable_wifi)
      printf '%s' "${CLEANSCOUT_PORTABLE_PC_IP}"
      ;;
    phone_hotspot)
      cleanscout_host_from_suffix "${current_ip}" "${phone_suffix}"
      ;;
  esac
}

cleanscout_print_network() {
  local current_ip
  local pi_host
  local pc_host

  current_ip="$(cleanscout_current_ipv4)"
  if [ -z "${current_ip}" ]; then
    printf 'Failed to detect local IPv4 address\n' >&2
    return 1
  fi

  pi_host="$(cleanscout_pi_host "${current_ip}")"
  pc_host="$(cleanscout_pc_host "${current_ip}")"

  printf 'network_mode=%s\n' "${CLEANSCOUT_NETWORK_MODE}"
  printf 'local_ip=%s\n' "${current_ip}"
  printf 'pi_host=%s\n' "${pi_host}"
  printf 'pc_host=%s\n' "${pc_host}"
  if [ "${CLEANSCOUT_NETWORK_MODE}" = "portable_wifi" ]; then
    printf 'ssid=%s\n' "${CLEANSCOUT_PORTABLE_SSID}"
    printf 'gateway=%s\n' "${CLEANSCOUT_PORTABLE_GATEWAY}"
    printf 'orangepi_host=%s\n' "${CLEANSCOUT_PORTABLE_ORANGEPI_IP}"
  fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  cleanscout_print_network
fi
