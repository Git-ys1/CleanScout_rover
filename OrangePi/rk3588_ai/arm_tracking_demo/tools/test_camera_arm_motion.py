#!/usr/bin/env python3
"""Verify yaw/pitch motion by measuring the end-camera image displacement."""

from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path

import cv2
import numpy as np
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


def capture_frame(camera_index: int, output: Path):
    capture = cv2.VideoCapture(camera_index, cv2.CAP_V4L2)
    capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    frame = None
    for _ in range(12):
        ok, current = capture.read()
        if ok and current is not None and current.size:
            frame = current
        time.sleep(0.03)
    capture.release()

    if frame is None:
        raise RuntimeError("camera returned no frame")
    output.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output), frame):
        raise RuntimeError("cannot write {}".format(output))
    return frame


def compare_frames(reference, current):
    difference = cv2.absdiff(reference, current)
    reference_gray = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY).astype(np.float32)
    current_gray = cv2.cvtColor(current, cv2.COLOR_BGR2GRAY).astype(np.float32)
    shift, response = cv2.phaseCorrelate(reference_gray, current_gray)
    result = {
        "mean_abs_diff": float(difference.mean()),
        "shift_x": float(shift[0]),
        "shift_y": float(shift[1]),
        "phase_response": float(response),
    }
    warp = np.eye(2, 3, dtype=np.float32)
    try:
        correlation, warp = cv2.findTransformECC(
            reference_gray / 255.0,
            current_gray / 255.0,
            warp,
            cv2.MOTION_AFFINE,
            (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6),
            None,
            5,
        )
        result.update(
            {
                "affine_correlation": float(correlation),
                "affine_rotation_deg": float(
                    math.degrees(math.atan2(float(warp[1, 0]), float(warp[0, 0])))
                ),
                "affine_tx": float(warp[0, 2]),
                "affine_ty": float(warp[1, 2]),
            }
        )
    except cv2.error as exc:
        result["affine_error"] = str(exc)
    return result


def offset_angle(driver, axis: str, pwm_offset: int):
    sign = float(driver.config["{}_pwm_sign".format(axis)])
    scale = float(driver.config["{}_pwm_per_rad".format(axis)])
    initial = float(driver.config["{}_init".format(axis)])
    return initial + float(pwm_offset) / (sign * scale)


def parse_ids(text: str):
    if not text.strip():
        return []
    result = [int(part.strip()) for part in text.split(",") if part.strip()]
    if any(servo_id < 0 or servo_id > 5 for servo_id in result):
        raise ValueError("--scan_ids is limited to the arm's Servo000-005")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(ROOT / "config/arm_track_config.yaml"))
    parser.add_argument("--serial_port", default="")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--dry_run", type=str2bool, default=True)
    parser.add_argument("--enable_arm", action="store_true")
    parser.add_argument("--pwm_offset", type=int, default=100)
    parser.add_argument(
        "--scan_ids",
        default="",
        help="comma-separated servo IDs to identify by camera motion, for example 1,2,3",
    )
    parser.add_argument("--duration_ms", type=int, default=800)
    parser.add_argument("--hold_s", type=float, default=1.0)
    parser.add_argument(
        "--output_dir",
        default=str(Path.home() / "rk3588_ai/debug_logs/arm_motion_probe"),
    )
    args = parser.parse_args()

    if not args.dry_run and not args.enable_arm:
        raise SystemExit("Real output requires --enable_arm --dry_run false")
    if abs(args.pwm_offset) > 150:
        raise SystemExit("--pwm_offset is limited to +/-150 for this safety test")

    with open(args.config, "r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    serial_cfg = dict(config.get("serial", {}))
    driver_cfg = dict(config.get("driver", {}))
    output_dir = Path(args.output_dir).expanduser()

    driver = ArmDriver(
        port=args.serial_port or serial_cfg.get("port", "/dev/ttyUSB0"),
        baudrate=int(serial_cfg.get("baudrate", 115200)),
        dry_run=args.dry_run,
        config=driver_cfg,
    )
    yaw_initial = float(driver.config["yaw_init"])
    pitch_initial = float(driver.config["pitch_init"])
    yaw_test = offset_angle(driver, "yaw", args.pwm_offset)
    pitch_test = offset_angle(driver, "pitch", args.pwm_offset)
    scan_ids = parse_ids(args.scan_ids)
    neutral_pwms = list(driver.config.get("hold_servo_pwms", [1500] * 6))

    driver.connect()
    try:
        baseline = capture_frame(args.camera, output_dir / "baseline.jpg")

        if scan_ids:
            for servo_id in scan_ids:
                neutral_pwm = int(neutral_pwms[servo_id])
                driver.set_servo_pwm(
                    servo_id,
                    neutral_pwm + args.pwm_offset,
                    args.duration_ms,
                )
                time.sleep(args.hold_s)
                frame = capture_frame(
                    args.camera,
                    output_dir / "servo_{:03d}_offset.jpg".format(servo_id),
                )
                driver.set_servo_pwm(servo_id, neutral_pwm, args.duration_ms)
                time.sleep(args.hold_s)
                print(
                    "servo_{:03d}_result={}".format(
                        servo_id,
                        compare_frames(baseline, frame),
                    )
                )
        else:
            driver.set_yaw(yaw_test, args.duration_ms)
            time.sleep(args.hold_s)
            yaw_frame = capture_frame(args.camera, output_dir / "yaw_offset.jpg")
            driver.set_yaw(yaw_initial, args.duration_ms)
            time.sleep(args.hold_s)

            driver.set_pitch(pitch_test, args.duration_ms)
            time.sleep(args.hold_s)
            pitch_frame = capture_frame(args.camera, output_dir / "pitch_offset.jpg")
            driver.set_pitch(pitch_initial, args.duration_ms)
            time.sleep(args.hold_s)

            print("yaw_result={}".format(compare_frames(baseline, yaw_frame)))
            print("pitch_result={}".format(compare_frames(baseline, pitch_frame)))
        print("images={}".format(output_dir))
    finally:
        try:
            for servo_id in scan_ids:
                driver.set_servo_pwm(
                    servo_id,
                    int(neutral_pwms[servo_id]),
                    args.duration_ms,
                )
            driver.set_yaw_pitch(yaw_initial, pitch_initial, args.duration_ms)
            time.sleep(max(0.2, args.duration_ms / 1000.0))
            driver.stop()
        finally:
            driver.close()


if __name__ == "__main__":
    main()
