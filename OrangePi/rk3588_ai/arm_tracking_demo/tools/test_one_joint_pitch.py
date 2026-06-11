#!/usr/bin/env python3
"""Small pitch-axis test. Defaults to dry-run; real output requires explicit flags."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from arm_driver import ArmDriver


def str2bool(value):
    text = str(value).strip().lower()
    if text in ("1", "true", "yes", "y", "on"):
        return True
    if text in ("0", "false", "no", "n", "off"):
        return False
    raise argparse.ArgumentTypeError("expected true/false")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(ROOT / "config/arm_track_config.yaml"))
    parser.add_argument("--serial_port", default="")
    parser.add_argument("--baudrate", type=int, default=0)
    parser.add_argument("--dry_run", type=str2bool, default=True)
    parser.add_argument("--enable_arm", action="store_true")
    parser.add_argument("--pitch", type=float, default=1.10)
    parser.add_argument("--duration_ms", type=int, default=300)
    parser.add_argument("--hold_s", type=float, default=0.8)
    args = parser.parse_args()

    if not args.dry_run and not args.enable_arm:
        raise SystemExit("Real output requires --enable_arm --dry_run false")

    with open(args.config, "r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    serial_cfg = config.get("serial", {})
    driver_cfg = config.get("driver", {})
    driver = ArmDriver(
        args.serial_port or serial_cfg.get("port", "/dev/ttyUSB0"),
        args.baudrate or int(serial_cfg.get("baudrate", 115200)),
        dry_run=args.dry_run,
        config=driver_cfg,
    )
    driver.connect()
    driver.set_pitch(args.pitch, args.duration_ms)
    time.sleep(max(args.hold_s, args.duration_ms / 1000.0 + 0.1))
    driver.stop([int(driver.config["pitch_servo_index"])])
    driver.close()


if __name__ == "__main__":
    main()
