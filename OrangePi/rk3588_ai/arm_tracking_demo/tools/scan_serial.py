#!/usr/bin/env python3
"""List candidate serial devices for the mechanical-arm lower controller."""

from __future__ import annotations

import glob
import os


def main():
    patterns = ["/dev/ttyUSB*", "/dev/ttyACM*", "/dev/ttyAMA*", "/dev/ttyS*"]
    devices = []
    for pattern in patterns:
        devices.extend(sorted(glob.glob(pattern)))

    print("Candidate serial devices:")
    if not devices:
        print("  none")
    for device in devices:
        try:
            stat = os.stat(device)
            print("  {} mode={:o} uid={} gid={}".format(device, stat.st_mode & 0o777, stat.st_uid, stat.st_gid))
        except OSError as exc:
            print("  {} stat_error={}".format(device, exc))

    try:
        from serial.tools import list_ports  # type: ignore
    except Exception as exc:
        print("pyserial list_ports unavailable: {}".format(exc))
        return

    print("pyserial list_ports:")
    for port in list_ports.comports():
        print("  {} {} {}".format(port.device, port.description, port.hwid))


if __name__ == "__main__":
    main()
