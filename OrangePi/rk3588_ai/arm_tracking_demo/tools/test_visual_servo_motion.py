#!/usr/bin/env python3
"""Drive the real yaw/pitch chain with a deterministic synthetic target box."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from arm_driver import ArmDriver
from visual_servo import VisualServo, config_from_mapping
from test_camera_arm_motion import capture_frame, compare_frames, str2bool


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(ROOT / "config/arm_track_config.yaml"))
    parser.add_argument("--serial_port", default="")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--dry_run", type=str2bool, default=True)
    parser.add_argument("--enable_arm", action="store_true")
    parser.add_argument("--target_x", type=float, default=500.0)
    parser.add_argument("--target_y", type=float, default=360.0)
    parser.add_argument("--cycles", type=int, default=15)
    parser.add_argument("--duration_ms", type=int, default=200)
    parser.add_argument(
        "--output_dir",
        default=str(Path.home() / "rk3588_ai/debug_logs/visual_servo_motion"),
    )
    args = parser.parse_args()

    if not args.dry_run and not args.enable_arm:
        raise SystemExit("Real output requires --enable_arm --dry_run false")
    if args.cycles < 2 or args.cycles > 30:
        raise SystemExit("--cycles must be between 2 and 30")
    if not (0 <= args.target_x <= 640 and 0 <= args.target_y <= 480):
        raise SystemExit("synthetic target must stay inside the 640x480 frame")

    with open(args.config, "r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    serial_cfg = dict(config.get("serial", {}))
    driver_cfg = dict(config.get("driver", {}))
    servo = VisualServo(config_from_mapping(dict(config.get("visual_servo", {}))))
    driver = ArmDriver(
        port=args.serial_port or serial_cfg.get("port", "/dev/ttyUSB0"),
        baudrate=int(serial_cfg.get("baudrate", 115200)),
        dry_run=args.dry_run,
        config=driver_cfg,
    )
    output_dir = Path(args.output_dir).expanduser()
    half_size = 40.0
    target_box = [
        args.target_x - half_size,
        args.target_y - half_size,
        args.target_x + half_size,
        args.target_y + half_size,
    ]

    driver.connect()
    try:
        baseline = capture_frame(args.camera, output_dir / "baseline.jpg")
        period = 1.0 / max(servo.config.control_rate_hz, 0.1)
        now = 1.0
        sent = 0
        for _ in range(args.cycles):
            result = servo.update(target_box, 640, 480, now=now)
            now += period + 0.001
            if result["should_send"]:
                driver.set_yaw_pitch(
                    result["yaw"],
                    result["pitch"],
                    duration_ms=args.duration_ms,
                )
                sent += 1
            time.sleep(period)

        moved = capture_frame(args.camera, output_dir / "after_synthetic_target.jpg")
        print("sent_cycles={}".format(sent))
        print("final_yaw={:.4f}".format(float(servo.last_result["yaw"])))
        print("final_pitch={:.4f}".format(float(servo.last_result["pitch"])))
        print("motion_result={}".format(compare_frames(baseline, moved)))
        print("images={}".format(output_dir))
    finally:
        try:
            driver.set_yaw_pitch(
                float(driver.config["yaw_init"]),
                float(driver.config["pitch_init"]),
                duration_ms=800,
            )
            time.sleep(0.8)
            driver.stop()
        finally:
            driver.close()


if __name__ == "__main__":
    main()
