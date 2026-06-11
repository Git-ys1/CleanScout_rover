#!/usr/bin/env python3
"""Read/write probe for the mechanical-arm bus-servo ASCII protocol.

Examples:
  python3 tools/bus_servo_probe.py --serial_port /dev/ttyUSB0 --read position
  python3 tools/bus_servo_probe.py --serial_port /dev/ttyUSB0 --read all --ids 0-5
  python3 tools/bus_servo_probe.py --serial_port /dev/ttyUSB0 --command '#000PRAD!'
  python3 tools/bus_servo_probe.py --serial_port /dev/ttyUSB0 --listen_s 5
"""

from __future__ import annotations

import argparse
import json
import os
import time
from typing import Iterable, List


READ_COMMANDS = {
    "id": "PID",
    "version": "PVER",
    "position": "PRAD",
    "status": "PRTV",
}


def hex_bytes(payload: bytes) -> str:
    return " ".join("{:02x}".format(byte) for byte in payload)


def parse_ids(text: str) -> List[int]:
    result: List[int] = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_text, end_text = part.split("-", 1)
            start = int(start_text, 10)
            end = int(end_text, 10)
            step = 1 if end >= start else -1
            result.extend(range(start, end + step, step))
        else:
            result.append(int(part, 10))

    for servo_id in result:
        if servo_id < 0 or servo_id > 253:
            raise ValueError("servo id out of range: {}".format(servo_id))
    return result


def build_read_commands(read_kind: str, ids: Iterable[int]) -> List[str]:
    kinds = list(READ_COMMANDS.keys()) if read_kind == "all" else [read_kind]
    commands = []
    for servo_id in ids:
        for kind in kinds:
            suffix = READ_COMMANDS[kind]
            commands.append("#{:03d}{}!".format(int(servo_id), suffix))
    return commands


def read_response(serial_obj, timeout_s: float, idle_s: float) -> bytes:
    end_time = time.time() + timeout_s
    last_rx = time.time()
    chunks = []
    while time.time() < end_time:
        waiting = int(getattr(serial_obj, "in_waiting", 0))
        if waiting > 0:
            chunks.append(serial_obj.read(waiting))
            last_rx = time.time()
        elif chunks and (time.time() - last_rx) >= idle_s:
            break
        else:
            time.sleep(0.01)
    return b"".join(chunks)


def str2tri_state(value: str):
    text = str(value).strip().lower()
    if text in ("keep", "none", ""):
        return None
    if text in ("1", "true", "yes", "y", "on"):
        return True
    if text in ("0", "false", "no", "n", "off"):
        return False
    raise argparse.ArgumentTypeError("expected keep/true/false")


def apply_line_state(serial_obj, dtr, rts) -> None:
    if dtr is not None:
        serial_obj.dtr = bool(dtr)
    if rts is not None:
        serial_obj.rts = bool(rts)


def make_payload(command: str, append_crlf: bool) -> bytes:
    payload = command.encode("ascii")
    if append_crlf:
        payload += b"\r\n"
    return payload


def print_record(record) -> None:
    print(json.dumps(record, ensure_ascii=False), flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe bus-servo ASCII commands.")
    parser.add_argument("--serial_port", default="/dev/ttyUSB0")
    parser.add_argument("--baudrate", type=int, default=115200)
    parser.add_argument("--timeout", type=float, default=1.00)
    parser.add_argument("--idle", type=float, default=0.10)
    parser.add_argument("--delay", type=float, default=0.05)
    parser.add_argument("--listen_s", type=float, default=0.0, help="listen without sending when >0")
    parser.add_argument("--append_crlf", action="store_true", help="append CRLF after every command")
    parser.add_argument("--no_reset_input", action="store_true", help="do not clear pending RX bytes after opening")
    parser.add_argument("--dtr", type=str2tri_state, default=None, help="set DTR: keep/true/false")
    parser.add_argument("--rts", type=str2tri_state, default=None, help="set RTS: keep/true/false")
    parser.add_argument("--ids", default="0-5", help="servo ids, for example 0-5 or 0,3")
    parser.add_argument(
        "--read",
        choices=["position", "id", "version", "status", "all"],
        default="position",
        help="safe read command set used when --command is not provided",
    )
    parser.add_argument(
        "--command",
        action="append",
        help="raw ASCII command to send, for example '#000PRAD!'; can be repeated",
    )
    args = parser.parse_args()

    try:
        import serial  # type: ignore
    except Exception as exc:
        raise SystemExit(
            "pyserial missing. Install it with: "
            "~/rk3588_ai/rknn_lite_env/bin/python3 -m pip install pyserial"
        ) from exc

    commands = args.command if args.command else build_read_commands(args.read, parse_ids(args.ids))

    serial_options = {
        "port": args.serial_port,
        "baudrate": args.baudrate,
        "timeout": args.timeout,
        "write_timeout": args.timeout,
    }
    if os.name == "posix":
        # Prevent a tracker/probe pair from consuming each other's replies.
        serial_options["exclusive"] = True

    try:
        serial_obj = serial.Serial(**serial_options)
    except Exception as exc:
        print_record(
            {
                "port": args.serial_port,
                "baudrate": args.baudrate,
                "error": "{}: {}".format(type(exc).__name__, exc),
                "hint": "stop the tracker or other probe that already owns this serial port",
            }
        )
        return 2

    with serial_obj:
        apply_line_state(serial_obj, args.dtr, args.rts)
        try:
            if not args.no_reset_input:
                serial_obj.reset_input_buffer()
        except Exception:
            pass

        if args.listen_s > 0:
            response = read_response(serial_obj, args.listen_s, args.idle)
            print_record(
                {
                    "port": args.serial_port,
                    "baudrate": args.baudrate,
                    "listen_s": args.listen_s,
                    "rx_ascii": response.decode("ascii", errors="replace"),
                    "rx_hex": hex_bytes(response),
                    "rx_len": len(response),
                }
            )
            return 0

        for command in commands:
            payload = make_payload(command, args.append_crlf)
            record = {
                "port": args.serial_port,
                "baudrate": args.baudrate,
                "tx_ascii": payload.decode("ascii", errors="replace"),
                "tx_hex": hex_bytes(payload),
                "dtr": getattr(serial_obj, "dtr", None),
                "rts": getattr(serial_obj, "rts", None),
            }
            try:
                serial_obj.write(payload)
                serial_obj.flush()
                time.sleep(args.delay)
                response = read_response(serial_obj, args.timeout, args.idle)
                record.update(
                    {
                        "rx_ascii": response.decode("ascii", errors="replace"),
                        "rx_hex": hex_bytes(response),
                        "rx_len": len(response),
                    }
                )
            except Exception as exc:
                record["error"] = "{}: {}".format(type(exc).__name__, exc)
            print_record(record)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
