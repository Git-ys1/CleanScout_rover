#!/usr/bin/env python3
"""Dry-run smoke test for ArmDriver packet/text generation."""

from __future__ import annotations

import argparse
import sys
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
    parser.add_argument("--print_cmd", action="store_true")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    serial_cfg = config.get("serial", {})
    driver_cfg = config.get("driver", {})
    if "timeout_s" in serial_cfg:
        driver_cfg["timeout_s"] = serial_cfg["timeout_s"]

    driver = ArmDriver(
        args.serial_port or serial_cfg.get("port", "/dev/ttyS7"),
        args.baudrate or int(serial_cfg.get("baudrate", 115200)),
        dry_run=args.dry_run,
        config=driver_cfg,
    )
    driver.connect()
    payload = driver.set_yaw_pitch(0.0, 1.2, duration_ms=200)
    if args.print_cmd:
        print("payload_ascii={}".format(payload.decode("ascii", errors="replace")))
        print("payload_hex={}".format(" ".join("{:02x}".format(byte) for byte in payload)))
    driver.stop()
    driver.close()


if __name__ == "__main__":
    main()
