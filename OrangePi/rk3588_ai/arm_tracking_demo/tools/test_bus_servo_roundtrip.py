#!/usr/bin/env python3
"""One-command bus-servo RX/TX/move/readback/restore verification."""

from __future__ import annotations

import argparse
import json
import os
import re
import time


POSITION_RE = re.compile(r"#(?P<id>\d{3})P(?P<pwm>\d{4})!")


def parse_ids(text):
    result = [int(part.strip()) for part in text.split(",") if part.strip()]
    if not result or any(servo_id < 0 or servo_id > 253 for servo_id in result):
        raise ValueError("--ids must contain servo IDs in the range 0..253")
    return result


def hex_bytes(payload):
    return " ".join("{:02x}".format(byte) for byte in payload)


def read_response(serial_obj, timeout_s=1.0, idle_s=0.12):
    end_time = time.time() + timeout_s
    last_rx = time.time()
    chunks = []
    while time.time() < end_time:
        waiting = int(serial_obj.in_waiting)
        if waiting:
            chunks.append(serial_obj.read(waiting))
            last_rx = time.time()
        elif chunks and time.time() - last_rx >= idle_s:
            break
        else:
            time.sleep(0.01)
    return b"".join(chunks)


def transact(serial_obj, command, timeout_s=1.0, delay_s=0.05):
    payload = command.encode("ascii")
    serial_obj.write(payload)
    serial_obj.flush()
    time.sleep(delay_s)
    response = read_response(serial_obj, timeout_s=timeout_s)
    print(
        json.dumps(
            {
                "tx_ascii": command,
                "tx_hex": hex_bytes(payload),
                "rx_ascii": response.decode("ascii", errors="replace"),
                "rx_hex": hex_bytes(response),
                "rx_len": len(response),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return response.decode("ascii", errors="replace")


def read_position(serial_obj, servo_id, timeout_s):
    response = transact(serial_obj, "#{:03d}PRAD!".format(servo_id), timeout_s)
    match = POSITION_RE.search(response)
    if match is None or int(match.group("id")) != servo_id:
        raise RuntimeError("Servo{:03d} position reply missing or mismatched".format(servo_id))
    return int(match.group("pwm"))


def wait_for_position(
    serial_obj,
    servo_id,
    target,
    timeout_s,
    settle_timeout_s,
    tolerance,
):
    deadline = time.time() + settle_timeout_s
    last_position = None
    while time.time() < deadline:
        last_position = read_position(serial_obj, servo_id, timeout_s)
        if abs(last_position - target) <= tolerance:
            return last_position
        time.sleep(0.2)
    return last_position


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial_port", default="/dev/ttyUSB0")
    parser.add_argument("--baudrate", type=int, default=115200)
    parser.add_argument("--ids", default="0,1,2")
    parser.add_argument("--offset", type=int, default=100)
    parser.add_argument("--duration_ms", type=int, default=1000)
    parser.add_argument("--timeout", type=float, default=1.0)
    parser.add_argument("--tolerance", type=int, default=25)
    parser.add_argument(
        "--settle_timeout",
        type=float,
        default=4.0,
        help="maximum seconds to poll PRAD after each movement command",
    )
    args = parser.parse_args()

    if abs(args.offset) < 20 or abs(args.offset) > 150:
        raise SystemExit("--offset must be between +/-20 and +/-150")
    if args.duration_ms < 200 or args.duration_ms > 3000:
        raise SystemExit("--duration_ms must be between 200 and 3000")

    try:
        import serial  # type: ignore
    except Exception as exc:
        raise SystemExit("pyserial is required") from exc

    serial_options = {
        "port": args.serial_port,
        "baudrate": args.baudrate,
        "timeout": args.timeout,
        "write_timeout": args.timeout,
    }
    if os.name == "posix":
        serial_options["exclusive"] = True

    servo_ids = parse_ids(args.ids)
    summary = []
    serial_obj = serial.Serial(**serial_options)
    try:
        for servo_id in servo_ids:
            initial = read_position(serial_obj, servo_id, args.timeout)
            target = max(900, min(2100, initial + args.offset))
            transact(
                serial_obj,
                "#{:03d}P{:04d}T{:04d}!".format(
                    servo_id,
                    target,
                    args.duration_ms,
                ),
                args.timeout,
            )
            moved = wait_for_position(
                serial_obj,
                servo_id,
                target,
                args.timeout,
                args.settle_timeout,
                args.tolerance,
            )
            transact(
                serial_obj,
                "#{:03d}P{:04d}T{:04d}!".format(
                    servo_id,
                    initial,
                    args.duration_ms,
                ),
                args.timeout,
            )
            restored = wait_for_position(
                serial_obj,
                servo_id,
                initial,
                args.timeout,
                args.settle_timeout,
                args.tolerance,
            )
            passed = (
                abs(moved - target) <= args.tolerance
                and abs(restored - initial) <= args.tolerance
            )
            summary.append(
                {
                    "servo_id": servo_id,
                    "initial": initial,
                    "target": target,
                    "moved": moved,
                    "restored": restored,
                    "passed": passed,
                }
            )
    finally:
        serial_obj.close()

    print(json.dumps({"summary": summary}, ensure_ascii=False, indent=2))
    return 0 if all(item["passed"] for item in summary) else 1


if __name__ == "__main__":
    raise SystemExit(main())
