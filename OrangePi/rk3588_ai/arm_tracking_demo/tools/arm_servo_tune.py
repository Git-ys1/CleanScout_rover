#!/usr/bin/env python3
"""Interactive bus-servo tuner for the mechanical-arm tracking pose.

Examples:
  python3 tools/arm_servo_tune.py
  python3 tools/arm_servo_tune.py --read 0-5
  python3 tools/arm_servo_tune.py --set 2=2000,3=1480 --duration_ms 1200
  python3 tools/arm_servo_tune.py --nudge 2=-50,3=20
  python3 tools/arm_servo_tune.py --save-start-pose --ids 1-3
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


POSITION_RE = re.compile(r"#(?P<id>\d{3})P(?P<pwm>\d{4})!")
DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config" / "arm_track_config.yaml"


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


def parse_assignments(text: str) -> Dict[int, int]:
    result: Dict[int, int] = {}
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise ValueError("assignment must look like 2=2000")
        key, value = part.split("=", 1)
        servo_id = int(key.strip(), 10)
        pwm = int(value.strip(), 10)
        if servo_id < 0 or servo_id > 253:
            raise ValueError("servo id out of range: {}".format(servo_id))
        if pwm < 500 or pwm > 2500:
            raise ValueError("pwm out of safe tuning range 500..2500: {}".format(pwm))
        result[servo_id] = pwm
    if not result:
        raise ValueError("no assignments found")
    return result


def hex_bytes(payload: bytes) -> str:
    return " ".join("{:02x}".format(byte) for byte in payload)


def read_response(serial_obj, timeout_s: float = 0.8, idle_s: float = 0.08) -> bytes:
    end_time = time.time() + timeout_s
    last_rx = time.time()
    chunks = []
    while time.time() < end_time:
        waiting = int(getattr(serial_obj, "in_waiting", 0))
        if waiting:
            chunks.append(serial_obj.read(waiting))
            last_rx = time.time()
        elif chunks and time.time() - last_rx >= idle_s:
            break
        else:
            time.sleep(0.01)
    return b"".join(chunks)


def open_serial(port: str, baudrate: int, timeout_s: float):
    try:
        import serial  # type: ignore
    except Exception as exc:
        raise SystemExit(
            "pyserial missing. Install with: "
            "~/rk3588_ai/rknn_lite_env/bin/python3 -m pip install pyserial"
        ) from exc

    options = {
        "port": port,
        "baudrate": baudrate,
        "timeout": timeout_s,
        "write_timeout": timeout_s,
    }
    if os.name == "posix":
        options["exclusive"] = True
    return serial.Serial(**options)


def transact(serial_obj, command: str, timeout_s: float = 0.8, delay_s: float = 0.05) -> str:
    payload = command.encode("ascii")
    serial_obj.write(payload)
    serial_obj.flush()
    time.sleep(delay_s)
    response = read_response(serial_obj, timeout_s=timeout_s)
    return response.decode("ascii", errors="replace")


def read_positions(serial_obj, ids: Iterable[int], timeout_s: float = 0.8) -> Dict[int, Optional[int]]:
    positions: Dict[int, Optional[int]] = {}
    for servo_id in ids:
        response = transact(serial_obj, "#{:03d}PRAD!".format(int(servo_id)), timeout_s=timeout_s)
        match = POSITION_RE.search(response)
        positions[int(servo_id)] = int(match.group("pwm")) if match else None
    return positions


def pack_move(assignments: Dict[int, int], duration_ms: int) -> str:
    commands = [
        "#{:03d}P{:04d}T{:04d}!".format(servo_id, pwm, int(duration_ms))
        for servo_id, pwm in sorted(assignments.items())
    ]
    return commands[0] if len(commands) == 1 else "{" + "".join(commands) + "}"


def move_servos(serial_obj, assignments: Dict[int, int], duration_ms: int, timeout_s: float) -> str:
    command = pack_move(assignments, duration_ms)
    response = transact(serial_obj, command, timeout_s=timeout_s)
    print(
        json.dumps(
            {
                "tx_ascii": command,
                "tx_hex": hex_bytes(command.encode("ascii")),
                "rx_ascii": response,
                "assignments": assignments,
                "duration_ms": duration_ms,
            },
            ensure_ascii=False,
        )
    )
    return response


def load_yaml(path: Path):
    try:
        import yaml  # type: ignore
    except Exception as exc:
        raise SystemExit("PyYAML is required in this environment") from exc
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def dump_yaml(path: Path, data) -> None:
    import yaml  # type: ignore

    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, allow_unicode=True, sort_keys=False)


def build_tracking_stages(positions: Dict[int, int], duration_ms: int) -> List[Dict[str, object]]:
    stage_main = {key: positions[key] for key in sorted(positions) if key in (1, 2)}
    stage_end = {key: positions[key] for key in sorted(positions) if key not in (1, 2)}
    stages: List[Dict[str, object]] = []
    if stage_main:
        stages.append({"pwms": stage_main, "duration_ms": max(duration_ms, 3000), "settle_s": 1.0})
    if stage_end:
        stages.append({"pwms": stage_end, "duration_ms": max(min(duration_ms, 3000), 1500), "settle_s": 0.8})
    return stages


def save_start_pose(config_path: Path, positions: Dict[int, int], duration_ms: int) -> None:
    config_path = config_path.resolve()
    data = load_yaml(config_path)
    driver = data.setdefault("driver", {})
    tracking_pose = {int(key): int(value) for key, value in sorted(positions.items())}

    driver["prepare_tracking_pose"] = True
    driver["tracking_pose_pwms"] = tracking_pose
    driver["tracking_pose_duration_ms"] = int(duration_ms)
    driver["tracking_pose_settle_s"] = float(driver.get("tracking_pose_settle_s", 4.0))
    driver["tracking_pose_stages"] = build_tracking_stages(tracking_pose, int(duration_ms))

    hold_pwms = list(driver.get("hold_servo_pwms", [1500] * 6))
    if len(hold_pwms) < 6:
        hold_pwms.extend([1500] * (6 - len(hold_pwms)))
    for servo_id, pwm in tracking_pose.items():
        if 0 <= servo_id < len(hold_pwms):
            hold_pwms[servo_id] = int(pwm)
    driver["hold_servo_pwms"] = hold_pwms

    if 0 in tracking_pose:
        driver["yaw_pwm_neutral"] = int(tracking_pose[0])
    if 3 in tracking_pose:
        driver["pitch_pwm_neutral"] = int(tracking_pose[3])

    backup_path = config_path.with_suffix(config_path.suffix + ".bak")
    shutil.copy2(str(config_path), str(backup_path))
    dump_yaml(config_path, data)
    print(
        json.dumps(
            {
                "saved_config": str(config_path),
                "backup": str(backup_path),
                "tracking_pose_pwms": tracking_pose,
                "tracking_pose_stages": driver["tracking_pose_stages"],
                "yaw_pwm_neutral": driver.get("yaw_pwm_neutral"),
                "pitch_pwm_neutral": driver.get("pitch_pwm_neutral"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def print_positions(positions: Dict[int, Optional[int]]) -> None:
    print(json.dumps({"positions": positions}, ensure_ascii=False, indent=2))


def interactive(args) -> int:
    with open_serial(args.serial_port, args.baudrate, args.timeout) as serial_obj:
        known_positions: Dict[int, int] = {}
        print("Arm servo tuner connected: {} @ {}".format(args.serial_port, args.baudrate))
        print("Commands: read [0-5] | set 2=2000,3=1480 [ms] | nudge 2=-50 [ms] | save [1-3] | quit")
        while True:
            try:
                line = input("servo> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return 0
            if not line:
                continue
            if line in ("q", "quit", "exit"):
                return 0
            try:
                parts = line.split()
                command = parts[0].lower()
                if command in ("r", "read"):
                    ids = parse_ids(parts[1] if len(parts) > 1 else args.ids)
                    current = read_positions(serial_obj, ids, timeout_s=args.timeout)
                    known_positions.update({servo_id: pwm for servo_id, pwm in current.items() if pwm is not None})
                    print_positions(current)
                elif command in ("s", "set"):
                    if len(parts) < 2:
                        print("usage: set 2=2000,3=1480 [duration_ms]")
                        continue
                    duration_ms = int(parts[2]) if len(parts) > 2 else args.duration_ms
                    assignments = parse_assignments(parts[1])
                    move_servos(serial_obj, assignments, duration_ms, args.timeout)
                    known_positions.update(assignments)
                elif command in ("n", "nudge"):
                    if len(parts) < 2:
                        print("usage: nudge 2=-50,3=20 [duration_ms]")
                        continue
                    duration_ms = int(parts[2]) if len(parts) > 2 else args.duration_ms
                    deltas = parse_assignments(parts[1])
                    current = read_positions(serial_obj, deltas.keys(), timeout_s=args.timeout)
                    known_positions.update({servo_id: pwm for servo_id, pwm in current.items() if pwm is not None})
                    assignments = {}
                    for servo_id, delta in deltas.items():
                        base = current[servo_id] if current[servo_id] is not None else known_positions.get(servo_id)
                        if base is None:
                            raise RuntimeError("cannot read current position for servo {}".format(servo_id))
                        assignments[servo_id] = int(base) + int(delta)
                    move_servos(serial_obj, assignments, duration_ms, args.timeout)
                    known_positions.update(assignments)
                elif command == "save":
                    ids = parse_ids(parts[1] if len(parts) > 1 else args.ids)
                    current = read_positions(serial_obj, ids, timeout_s=args.timeout)
                    positions = {}
                    for servo_id, pwm in current.items():
                        if pwm is not None:
                            positions[servo_id] = pwm
                        elif servo_id in known_positions:
                            positions[servo_id] = known_positions[servo_id]
                    if not positions:
                        print("no positions could be read; not saving")
                        continue
                    save_start_pose(Path(args.config), positions, args.duration_ms)
                else:
                    print("unknown command: {}".format(command))
            except Exception as exc:
                print("ERR: {}".format(exc))


def main() -> int:
    parser = argparse.ArgumentParser(description="Tune and save mechanical-arm bus-servo positions.")
    parser.add_argument("--serial_port", default="/dev/ttyUSB0")
    parser.add_argument("--baudrate", type=int, default=115200)
    parser.add_argument("--timeout", type=float, default=0.8)
    parser.add_argument("--duration_ms", type=int, default=1500)
    parser.add_argument("--ids", default="1-3")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--read", nargs="?", const="1-3", help="read positions, for example --read 0-5")
    parser.add_argument("--set", dest="set_values", help="set positions, for example --set 2=2000,3=1480")
    parser.add_argument("--nudge", help="nudge positions relative to current, for example --nudge 2=-50")
    parser.add_argument("--save-start-pose", action="store_true", help="read --ids and save them as startup pose")
    parser.add_argument("--values", help="save explicit startup values, for example --values 1=1700,2=2000,3=1480")
    args = parser.parse_args()

    if args.duration_ms < 100 or args.duration_ms > 10000:
        raise SystemExit("--duration_ms must be 100..10000")

    if not any((args.read, args.set_values, args.nudge, args.save_start_pose, args.values)):
        return interactive(args)

    known_positions: Dict[int, int] = parse_assignments(args.values) if args.values else {}

    if args.values and not any((args.read, args.set_values, args.nudge)):
        if not args.save_start_pose:
            raise SystemExit("--values is only useful with --save-start-pose")
        save_start_pose(Path(args.config), known_positions, args.duration_ms)
        return 0

    with open_serial(args.serial_port, args.baudrate, args.timeout) as serial_obj:
        if args.read:
            current = read_positions(serial_obj, parse_ids(args.read), timeout_s=args.timeout)
            known_positions.update({servo_id: pwm for servo_id, pwm in current.items() if pwm is not None})
            print_positions(current)
        if args.set_values:
            assignments = parse_assignments(args.set_values)
            move_servos(serial_obj, assignments, args.duration_ms, args.timeout)
            known_positions.update(assignments)
        if args.nudge:
            deltas = parse_assignments(args.nudge)
            current = read_positions(serial_obj, deltas.keys(), timeout_s=args.timeout)
            known_positions.update({servo_id: pwm for servo_id, pwm in current.items() if pwm is not None})
            assignments = {}
            for servo_id, delta in deltas.items():
                base = current[servo_id] if current[servo_id] is not None else known_positions.get(servo_id)
                if base is None:
                    raise SystemExit("cannot read current position for servo {}".format(servo_id))
                assignments[servo_id] = int(base) + int(delta)
            move_servos(serial_obj, assignments, args.duration_ms, args.timeout)
            known_positions.update(assignments)
        if args.save_start_pose:
            current = read_positions(serial_obj, parse_ids(args.ids), timeout_s=args.timeout)
            positions = {}
            for servo_id, pwm in current.items():
                if pwm is not None:
                    positions[servo_id] = pwm
                elif servo_id in known_positions:
                    positions[servo_id] = known_positions[servo_id]
            if not positions:
                raise SystemExit("no positions could be read; not saving")
            save_start_pose(Path(args.config), positions, args.duration_ms)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
