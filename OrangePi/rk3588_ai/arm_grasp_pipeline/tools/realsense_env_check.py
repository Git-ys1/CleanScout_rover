#!/usr/bin/env python3
"""Check the OrangePi RealSense runtime before running D430/D435 smoke tests."""
from __future__ import annotations

import glob
import os
import subprocess
import sys


def run_text(cmd):
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        return out.strip()
    except Exception as exc:
        return f"<failed: {exc}>"


def main() -> int:
    print("python:", sys.version.replace("\n", " "))
    print("executable:", sys.executable)

    print("\n[usb]")
    lsusb = run_text(["lsusb"])
    print(lsusb or "<no lsusb output>")
    intel_lines = [line for line in lsusb.splitlines() if "8086:" in line or "Intel" in line or "RealSense" in line]
    if intel_lines:
        print("intel_realsense_usb: yes")
        for line in intel_lines:
            print("  ", line)
    else:
        print("intel_realsense_usb: not detected")

    print("\n[video]")
    video_nodes = sorted(glob.glob("/dev/video*"))
    if video_nodes:
        for node in video_nodes:
            try:
                st = os.stat(node)
                print(f"{node} mode={oct(st.st_mode & 0o777)}")
            except OSError as exc:
                print(f"{node} <stat failed: {exc}>")
    else:
        print("<no /dev/video* nodes>")

    print("\n[pyrealsense2]")
    try:
        import pyrealsense2 as rs  # type: ignore
    except Exception as exc:
        print("pyrealsense2: unavailable")
        print("error:", repr(exc))
        print("next: install/enable Intel RealSense runtime before D430/D435 smoke tests")
        return 2

    print("pyrealsense2: ok")
    try:
        ctx = rs.context()
        devices = list(ctx.query_devices())
        print("device_count:", len(devices))
        for dev in devices:
            def info(kind):
                try:
                    return dev.get_info(kind)
                except Exception:
                    return "<unknown>"

            print(
                "device:",
                info(rs.camera_info.name),
                "serial:",
                info(rs.camera_info.serial_number),
                "firmware:",
                info(rs.camera_info.firmware_version),
            )
        return 0 if devices else 3
    except Exception as exc:
        print("pyrealsense2 query failed:", repr(exc))
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
