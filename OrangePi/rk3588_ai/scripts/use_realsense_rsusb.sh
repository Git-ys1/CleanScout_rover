#!/usr/bin/env bash
# Use the isolated librealsense 2.56.5 RSUSB runtime built for OrangePi Python 3.8.

RSUSB_ROOT="${HOME}/rk3588_ai/librealsense-rsusb-2.56.5"

if [[ ! -f "${RSUSB_ROOT}/python/pyrealsense2.cpython-38-aarch64-linux-gnu.so" ]]; then
    echo "RealSense RSUSB Python module is missing: ${RSUSB_ROOT}/python" >&2
    return 1 2>/dev/null || exit 1
fi

export PYTHONPATH="${RSUSB_ROOT}/python${PYTHONPATH:+:${PYTHONPATH}}"
export LD_LIBRARY_PATH="${RSUSB_ROOT}/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"

echo "RealSense RSUSB 2.56.5 environment enabled"
