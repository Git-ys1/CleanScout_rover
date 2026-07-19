#!/usr/bin/env python3
"""Measure Servo001..003 PWM/degree from a visible horizontal table.

The D435 is rigidly attached to the arm. For the three parallel pitch joints,
changing one joint rotates the camera by the same angle. Fitting the table
normal before and after a small PWM step therefore gives an independent
physical angle measurement without trusting the current FK model.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.realsense_source import D435Source
from arm_grasp_pipeline.serial_servo_adapter import SerialServoArmAdapter


CONTROLLER_PWM_MIN = 500
CONTROLLER_PWM_MAX = 2490


def parse_ints(text, expected=None):
    values = [int(part.strip()) for part in str(text).split(",") if part.strip()]
    if expected is not None and len(values) != expected:
        raise ValueError("expected {} comma-separated integers".format(expected))
    return values


def parse_roi(text):
    values = parse_ints(text, expected=4)
    x1, y1, x2, y2 = values
    if x1 < 0 or y1 < 0 or x2 <= x1 or y2 <= y1:
        raise ValueError("ROI must be x1,y1,x2,y2 with positive area")
    return tuple(values)


def _depth_points(depth_m, intrinsics, roi, stride):
    depth = np.asarray(depth_m, dtype=float)
    x1, y1, x2, y2 = roi
    if x2 > depth.shape[1] or y2 > depth.shape[0]:
        raise ValueError("ROI exceeds depth image bounds")
    ys, xs = np.mgrid[y1:y2:stride, x1:x2:stride]
    z = depth[y1:y2:stride, x1:x2:stride]
    valid = np.isfinite(z) & (z > 0.12) & (z < 1.20)
    if np.count_nonzero(valid) < 300:
        raise RuntimeError("not enough valid depth samples in ROI")
    z = z[valid]
    x = (xs[valid] - float(intrinsics.cx)) * z / float(intrinsics.fx)
    y = (ys[valid] - float(intrinsics.cy)) * z / float(intrinsics.fy)
    return np.column_stack((x, y, z))


def _refine_plane(points):
    center = np.mean(points, axis=0)
    _, _, vh = np.linalg.svd(points - center, full_matrices=False)
    normal = vh[-1]
    normal = normal / np.linalg.norm(normal)
    return center, normal


def fit_plane_normal(depth_m, intrinsics, roi, stride=2):
    """Fit a robust plane normal to an aligned-depth ROI."""
    points = _depth_points(depth_m, intrinsics, roi, stride)

    for threshold_m in (0.010, 0.006, 0.004):
        center, normal = _refine_plane(points)
        distances = np.abs((points - center) @ normal)
        kept = points[distances <= threshold_m]
        if kept.shape[0] >= 300:
            points = kept

    center, normal = _refine_plane(points)
    if normal[2] > 0.0:
        normal = -normal
    residuals = np.abs((points - center) @ normal)
    return normal, float(np.sqrt(np.mean(residuals ** 2))), int(points.shape[0])


def fit_dominant_plane_normal(depth_m, intrinsics, roi, normal_hint,
                              stride=3, iterations=180,
                              inlier_threshold_m=0.005,
                              max_hint_angle_deg=30.0):
    """Find the largest table-like plane after arm motion changes the view."""
    points = _depth_points(depth_m, intrinsics, roi, stride)
    hint = np.asarray(normal_hint, dtype=float)
    hint = hint / np.linalg.norm(hint)
    min_dot = math.cos(math.radians(float(max_hint_angle_deg)))
    rng = np.random.default_rng(525)
    best_mask = None
    best_count = 0

    for _ in range(int(iterations)):
        indices = rng.choice(points.shape[0], size=3, replace=False)
        p0, p1, p2 = points[indices]
        normal = np.cross(p1 - p0, p2 - p0)
        length = float(np.linalg.norm(normal))
        if length < 1e-8:
            continue
        normal = normal / length
        if float(np.dot(normal, hint)) < 0.0:
            normal = -normal
        if float(np.dot(normal, hint)) < min_dot:
            continue
        distance = np.abs((points - p0) @ normal)
        mask = distance <= float(inlier_threshold_m)
        count = int(np.count_nonzero(mask))
        if count > best_count:
            best_count = count
            best_mask = mask

    if best_mask is None or best_count < 1000:
        raise RuntimeError(
            "no dominant table plane found; best inliers={}".format(best_count)
        )
    inliers = points[best_mask]
    for threshold_m in (0.005, 0.0035):
        center, normal = _refine_plane(inliers)
        if float(np.dot(normal, hint)) < 0.0:
            normal = -normal
        distances = np.abs((points - center) @ normal)
        selected = points[distances <= threshold_m]
        if selected.shape[0] >= 1000:
            inliers = selected
    center, normal = _refine_plane(inliers)
    if float(np.dot(normal, hint)) < 0.0:
        normal = -normal
    residuals = np.abs((inliers - center) @ normal)
    return normal, float(np.sqrt(np.mean(residuals ** 2))), int(inliers.shape[0])


def capture_table_normal(source, roi, frame_count, normal_hint=None):
    normals = []
    rms_values = []
    counts = []
    for _ in range(8):
        source.read()
    for _ in range(int(frame_count)):
        frame = source.read()
        if normal_hint is None:
            normal, rms_m, point_count = fit_plane_normal(
                frame.depth_m, frame.intrinsics_for_detection, roi
            )
        else:
            normal, rms_m, point_count = fit_dominant_plane_normal(
                frame.depth_m,
                frame.intrinsics_for_detection,
                roi,
                normal_hint,
            )
        if normals and float(np.dot(normals[0], normal)) < 0.0:
            normal = -normal
        normals.append(normal)
        rms_values.append(rms_m)
        counts.append(point_count)
    normal = np.mean(np.asarray(normals), axis=0)
    normal = normal / np.linalg.norm(normal)
    return {
        "normal_camera": [float(value) for value in normal],
        "plane_rmse_m": float(np.median(rms_values)),
        "point_count": int(np.median(counts)),
    }


def normal_angle_deg(first, second):
    a = np.asarray(first, dtype=float)
    b = np.asarray(second, dtype=float)
    dot = float(np.clip(np.dot(a, b), -1.0, 1.0))
    return math.degrees(math.acos(dot))


def require_pose(adapter, expected, tolerance_pwm):
    actual = adapter.read_pwms(range(6), timeout_s=0.8)
    mismatches = {}
    for servo_id, target in enumerate(expected):
        value = actual.get(servo_id)
        if value is None or abs(int(value) - int(target)) > int(tolerance_pwm):
            mismatches[str(servo_id)] = {
                "target": int(target),
                "actual": None if value is None else int(value),
            }
    if mismatches:
        raise RuntimeError("reference pose mismatch: " + json.dumps(mismatches))
    return actual


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial_port", default="/dev/ttyUSB0")
    parser.add_argument("--baudrate", type=int, default=115200)
    parser.add_argument("--reference_pwms", default="1500,1909,1900,620,1500,1500")
    parser.add_argument("--servo_ids", default="1,2,3")
    parser.add_argument("--delta_pwm", type=int, default=100)
    parser.add_argument("--duration_ms", type=int, default=2200)
    parser.add_argument("--settle_s", type=float, default=0.6)
    parser.add_argument("--tolerance_pwm", type=int, default=40)
    parser.add_argument("--roi", default="40,260,280,460")
    parser.add_argument("--probe_roi", default="0,100,640,480")
    parser.add_argument("--frames", type=int, default=8)
    parser.add_argument("--output_json", default="")
    parser.add_argument("--enable_arm", action="store_true")
    args = parser.parse_args()

    if not args.enable_arm:
        raise SystemExit("refusing motion without --enable_arm")
    reference = parse_ints(args.reference_pwms, expected=6)
    servo_ids = parse_ints(args.servo_ids)
    if not servo_ids or any(value not in (1, 2, 3) for value in servo_ids):
        raise ValueError("--servo_ids must contain only 1,2,3")
    if args.delta_pwm == 0 or abs(args.delta_pwm) > 250:
        raise ValueError("--delta_pwm must be non-zero and at most 250")
    ticks = max(1.0, float(args.duration_ms) / 20.0)
    if abs(float(args.delta_pwm)) / ticks < 1.05:
        raise ValueError(
            "PWM step/duration would produce a sub-1 PWM tick in the STM32 "
            "uint16 ramp; increase delta or shorten duration"
        )
    roi = parse_roi(args.roi)
    probe_roi = parse_roi(args.probe_roi)

    adapter = SerialServoArmAdapter(
        port=args.serial_port, baudrate=args.baudrate, dry_run=False
    )
    source = D435Source(640, 480, 30)
    adapter.connect()
    source.start()
    report = {
        "reference_pwms": reference,
        "delta_pwm_requested": int(args.delta_pwm),
        "roi_xyxy": list(roi),
        "probe_roi_xyxy": list(probe_roi),
        "measurements": [],
    }
    try:
        report["reference_readback"] = require_pose(
            adapter, reference, args.tolerance_pwm
        )
        baseline = capture_table_normal(source, roi, args.frames)
        report["baseline"] = baseline
        print("TABLE_BASELINE " + json.dumps(baseline))

        for servo_id in servo_ids:
            target = int(reference[servo_id]) + int(args.delta_pwm)
            if target < CONTROLLER_PWM_MIN or target > CONTROLLER_PWM_MAX:
                raise ValueError(
                    "Servo{:03d} probe target {} outside controller range {}..{}".format(
                        servo_id, target, CONTROLLER_PWM_MIN, CONTROLLER_PWM_MAX
                    )
                )
            adapter.send_partial_pwm_command({servo_id: target}, args.duration_ms)
            time.sleep(args.duration_ms / 1000.0 + args.settle_s)
            readback = adapter.read_pwms(range(6), timeout_s=0.8)
            actual = readback.get(servo_id)
            if actual is None or abs(int(actual) - target) > args.tolerance_pwm:
                raise RuntimeError(
                    "Servo{:03d} probe did not reach target: {}".format(
                        servo_id, json.dumps(readback)
                    )
                )
            moved = capture_table_normal(
                source,
                probe_roi,
                args.frames,
                normal_hint=baseline["normal_camera"],
            )
            angle_deg = normal_angle_deg(
                baseline["normal_camera"], moved["normal_camera"]
            )
            actual_delta = int(actual) - int(report["reference_readback"][servo_id])
            if angle_deg < 0.25:
                raise RuntimeError("measured table-normal angle is too small")
            measurement = {
                "servo_id": int(servo_id),
                "target_pwm": target,
                "actual_pwm": int(actual),
                "actual_delta_pwm": actual_delta,
                "angle_deg": float(angle_deg),
                "pwm_per_deg": abs(float(actual_delta)) / float(angle_deg),
                "moved_plane": moved,
            }
            report["measurements"].append(measurement)
            print("JOINT_PITCH_MEASUREMENT " + json.dumps(measurement))

            adapter.send_partial_pwm_command(
                {servo_id: reference[servo_id]}, args.duration_ms
            )
            time.sleep(args.duration_ms / 1000.0 + args.settle_s)
            require_pose(adapter, reference, args.tolerance_pwm)
    finally:
        try:
            adapter.send_pwm_command(reference, 2500)
            time.sleep(2.5 + args.settle_s)
        except Exception as exc:
            print("RESTORE_WARNING " + str(exc), file=sys.stderr)
        adapter.close()
        source.stop()

    if args.output_json:
        path = Path(args.output_json).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
