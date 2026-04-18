#!/usr/bin/env python3

import argparse
import time

import serial


DEFAULT_DEV = "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0"
DEFAULT_FALLBACK_DEV = "/dev/ttyUSB0"
DEFAULT_BAUD = 115200
DEFAULT_SEND_HZ = 50.0


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


def connect(devices, baud, timeout):
    last_error = None
    for device in devices:
        try:
            print(f"OPEN: {device} @ {baud}")
            return serial.Serial(device, baud, timeout=timeout), device
        except (OSError, serial.SerialException) as exc:
            last_error = exc
            print(f"OPEN FAIL: {device}: {exc}")
    if last_error is None:
        raise serial.SerialException("no serial device configured")
    raise last_error


def send(ser, cmd):
    print(f"TX: {cmd}")
    ser.write((cmd + "\n").encode())
    ser.flush()


def send_w_stream(ser, vx, sec, send_hz):
    period = 1.0 / send_hz
    deadline = time.time() + sec
    sent = 0
    while time.time() < deadline:
        send(ser, f"W,{vx:.3f},{vx:.3f},{vx:.3f},{vx:.3f}")
        drain(ser, min(0.08, period))
        sent += 1
        sleep_sec = period - 0.08
        if sleep_sec > 0.0:
            time.sleep(sleep_sec)
    return sent


def main():
    parser = argparse.ArgumentParser(description="OpenRF1 minimal bridge smoke test")
    parser.add_argument("--dev", default=DEFAULT_DEV, help="preferred serial device path")
    parser.add_argument("--fallback-dev", default=DEFAULT_FALLBACK_DEV, help="fallback serial device path")
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD, help="baudrate")
    parser.add_argument("--timeout", type=float, default=0.2, help="serial read timeout")
    parser.add_argument("--send-hz", type=float, default=DEFAULT_SEND_HZ, help="continuous W send rate")
    parser.add_argument("--stream-sec", type=float, default=1.0, help="seconds to stream W frames")
    parser.add_argument("--wheel-ms", type=float, default=0.08, help="per-wheel target speed in m/s")
    parser.add_argument("--encoder-channel", type=int, default=2, help="channel for E command")
    parser.add_argument("--motor-channel", type=int, default=2, help="channel for M command")
    parser.add_argument("--motor-pwm", type=int, default=300, help="PWM value for M command")
    args = parser.parse_args()

    ser, actual_device = connect([args.dev, args.fallback_dev], args.baud, args.timeout)
    print(f"USING: {actual_device}")
    time.sleep(0.3)

    print("=== startup drain ===")
    drain(ser, 1.0)

    print("=== debug commands ===")
    send(ser, "STOP")
    drain(ser, 0.4)
    send(ser, f"E,{args.encoder_channel}")
    drain(ser, 0.4)
    send(ser, f"M,{args.motor_channel},{args.motor_pwm}")
    drain(ser, 0.8)
    send(ser, "STOP")
    drain(ser, 0.4)

    print("=== continuous W stream ===")
    sent = send_w_stream(ser, args.wheel_ms, args.stream_sec, args.send_hz)
    print(f"STREAM SENT: {sent} frames")

    print("=== shutdown ===")
    send(ser, "STOP")
    drain(ser, 0.5)
    ser.close()
    print("=== done ===")


if __name__ == "__main__":
    main()
