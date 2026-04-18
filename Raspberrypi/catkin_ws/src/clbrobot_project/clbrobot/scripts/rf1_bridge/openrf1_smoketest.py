#!/usr/bin/env python3

import argparse
import serial
import time


DEFAULT_DEV = "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0"
DEFAULT_BAUD = 115200


def drain(ser, sec):
    end = time.time() + sec
    lines = []
    while time.time() < end:
        line = ser.readline().decode(errors="ignore").strip()
        if line:
            lines.append(line)
            print(f"RX: {line}")
    if not lines:
        print("RX: <none>")
    return lines


def send(ser, cmd, wait):
    print(f"TX: {cmd}")
    ser.write((cmd + "\n").encode())
    ser.flush()
    return drain(ser, wait)


def main():
    parser = argparse.ArgumentParser(description="OpenRF1 USB serial smoke test")
    parser.add_argument("--dev", default=DEFAULT_DEV, help="serial device path")
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD, help="baudrate")
    args = parser.parse_args()

    ser = serial.Serial(args.dev, args.baud, timeout=0.2)
    time.sleep(0.3)

    print("=== open ===")
    drain(ser, 1.0)
    send(ser, "STOP", 0.5)
    send(ser, "E,2", 0.5)
    send(ser, "M,2,400", 1.0)
    send(ser, "STOP", 0.5)
    send(ser, "W,0.08,0.08,0.08,0.08", 1.2)
    send(ser, "STOP", 0.5)
    ser.close()
    print("=== done ===")


if __name__ == "__main__":
    main()
