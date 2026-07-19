#!/usr/bin/env python3
"""Validate fixed-view RGB-D target coordinates without importing or opening serial."""
from __future__ import annotations

import argparse
from collections import deque
import json
import math
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.fixed_view import (
    FixedViewCalibration,
    ObjectGeometry,
    fixed_view_target_debug,
    horizontal_approach_axis,
    pre_grasp_from_bottle_center,
)
from arm_grasp_pipeline.grasp_planner import (
    GraspConfig,
    build_fixed_view_grasp_plan,
    inside_workspace,
)
from arm_grasp_pipeline.official_kinematics import OfficialArmKinematics
from arm_grasp_pipeline.realsense_source import D435Source
from arm_grasp_pipeline.target_depth import median_depth_in_bbox, stable_bbox


DEFAULT_CONFIG = ROOT / "config/arm_grasp_default.json"
DEFAULT_YOLO_DIR = Path.home() / "rk3588_ai/rknn_model_zoo/examples/yolo11/python"


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--model_path", default="~/rk3588_ai/models/official_yolo11.rknn")
    parser.add_argument("--yolo_dir", default=str(DEFAULT_YOLO_DIR))
    parser.add_argument("--target", default="rk3588")
    parser.add_argument("--device_id", default=None)
    parser.add_argument("--target_class", default="")
    parser.add_argument("--conf", type=float, default=None)
    parser.add_argument("--strategy", choices=("nearest_center", "highest_conf"), default="")
    parser.add_argument("--max_frames", type=int, default=600)
    parser.add_argument("--max_results", type=int, default=1)
    parser.add_argument("--skip", type=int, default=0)
    parser.add_argument("--output_jsonl", default="")
    return parser.parse_args()


def load_config(path):
    with Path(path).expanduser().open("r", encoding="utf-8") as handle:
        return json.load(handle)


def ik_available(kinematics, xyz_m, pitch_deg):
    if xyz_m is None:
        return False
    return kinematics.inverse_pose(xyz_m, pitch_deg=pitch_deg, gripper=0.0) is not None


def minimum_reachable_center_radius(center_base_m, config, kinematics,
                                    resolution_m=0.001):
    """Return the first radial distance that passes the complete staged plan."""
    center = np.asarray(center_base_m, dtype=float)
    if center.shape != (3,) or not np.all(np.isfinite(center)):
        raise ValueError("center_base_m must contain three finite values")
    if not math.isfinite(resolution_m) or resolution_m <= 0.0:
        raise ValueError("resolution_m must be positive and finite")
    axis = horizontal_approach_axis(center)
    max_radius = math.hypot(
        max(abs(float(config.workspace_min_xyz_m[0])),
            abs(float(config.workspace_max_xyz_m[0]))),
        max(abs(float(config.workspace_min_xyz_m[1])),
            abs(float(config.workspace_max_xyz_m[1]))),
    )
    sample_count = int(math.ceil(max_radius / resolution_m))
    for sample_index in range(sample_count + 1):
        radius = sample_index * resolution_m
        candidate = np.array(
            [axis[0] * radius, axis[1] * radius, center[2]], dtype=float
        )
        try:
            build_fixed_view_grasp_plan(candidate, kinematics, config)
        except ValueError:
            continue
        return float(radius)
    return None


def build_validation_report(debug, config, kinematics, calibration):
    center = np.asarray(debug.bottle_center_base_m, dtype=float)
    axis = horizontal_approach_axis(center)
    pre = pre_grasp_from_bottle_center(center, config.pre_grasp_standoff_m)
    approach = center.copy()
    surface = np.asarray(debug.point_base_surface_m, dtype=float)
    workspace = {
        "point_base_surface": inside_workspace(surface, config),
        "bottle_center": inside_workspace(center, config),
        "pre_grasp": inside_workspace(pre, config),
        "approach": inside_workspace(approach, config),
    }
    ik_flags = {
        "point_base_surface": ik_available(kinematics, surface, config.pitch_deg),
        "bottle_center": ik_available(kinematics, center, config.pitch_deg),
        "pre_grasp": ik_available(kinematics, pre, config.pitch_deg),
        "approach": ik_available(kinematics, approach, config.pitch_deg),
    }
    plan_ok = True
    plan_error = ""
    try:
        build_fixed_view_grasp_plan(center, kinematics, config)
    except ValueError as exc:
        plan_ok = False
        plan_error = str(exc)
    current_radius = float(math.hypot(center[0], center[1]))
    minimum_radius = minimum_reachable_center_radius(center, config, kinematics)
    required_outward_shift = None
    if minimum_radius is not None:
        required_outward_shift = max(0.0, minimum_radius - current_radius)
    return {
        "pixel_xy": list(debug.pixel_xy),
        "depth_m": float(debug.depth_m),
        "point_camera_m": list(debug.point_camera_m),
        "point_base_surface_m": list(debug.point_base_surface_m),
        "bottle_center_base_m": list(debug.bottle_center_base_m),
        "pre_grasp_base_m": pre.tolist(),
        "approach_base_m": approach.tolist(),
        "approach_axis_base": axis.tolist(),
        "workspace_flags": workspace,
        "ik_flags": ik_flags,
        "plan_ok": plan_ok,
        "plan_error": plan_error,
        "configured_pitch_deg": float(config.pitch_deg),
        "l3_horizontal_commanded": abs(float(config.pitch_deg)) <= 1e-9,
        "current_center_radius_m": current_radius,
        "minimum_full_plan_center_radius_m": minimum_radius,
        "required_outward_shift_m": required_outward_shift,
        "reachability_hint_resolution_m": 0.001,
        "calibration_quality_pass": not bool(calibration.readiness_errors()),
        "serial_opened": False,
        "servo_command_sent": False,
    }


def main() -> int:
    args = parse_args()
    if args.max_frames < 1 or args.max_results < 1 or args.skip < 0:
        raise ValueError("max_frames/max_results must be positive and skip non-negative")
    config_data = load_config(args.config)
    calibration = FixedViewCalibration.from_mapping(
        dict(config_data.get("fixed_view_calibration", {}))
    )
    matrix = calibration.matrix()
    object_geometry = ObjectGeometry.from_mapping(
        dict(config_data.get("object_geometry", {}))
    )
    grasp_mapping = dict(config_data.get("grasp", {}))
    grasp_config = GraspConfig.from_mapping(grasp_mapping)
    kinematics_mapping = dict(config_data.get("kinematics", {}))
    joint_pwm_mapping = dict(config_data.get("joint_pwm_calibration", {}))
    required_kinematics = {
        "backend", "calibrated", "l0_m", "l1_m", "l2_m", "l3_m",
    }
    missing_kinematics = sorted(required_kinematics.difference(kinematics_mapping))
    if missing_kinematics:
        raise ValueError(
            "kinematics config missing fields: " + ", ".join(missing_kinematics)
        )
    if str(kinematics_mapping["backend"]) != "official_f103":
        raise ValueError("fixed-view validation requires the official_f103 kinematics backend")
    kinematics = OfficialArmKinematics.from_config(
        kinematics_mapping, joint_pwm_mapping
    )
    runtime = dict(config_data.get("runtime", {}))
    target_class = args.target_class or runtime.get("target_class", "bottle")
    confidence = args.conf if args.conf is not None else float(runtime.get("confidence", 0.25))
    strategy = args.strategy or runtime.get("selection_strategy", "nearest_center")
    realsense = dict(config_data.get("realsense", {}))

    from arm_grasp_pipeline.rknn_yolo_detector import RknnYolo11Detector

    detector = RknnYolo11Detector(
        args.model_path, args.yolo_dir, target=args.target, device_id=args.device_id,
        object_threshold=confidence,
    )
    source = D435Source(
        int(realsense.get("width", 640)),
        int(realsense.get("height", 480)),
        int(realsense.get("fps", 30)),
        serial_number=realsense.get("serial_number") or None,
    )
    output_path = Path(args.output_jsonl).expanduser() if args.output_jsonl else None
    output_handle = None
    bbox_history = deque(maxlen=max(10, grasp_config.stable_frames + 2))
    depth_history = deque(maxlen=max(3, grasp_config.depth_stable_frames))
    result_count = 0

    try:
        detector.start()
        source.start()
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_handle = output_path.open("w", encoding="utf-8")
        for frame_index in range(args.max_frames):
            frame = source.read()
            if frame_index % (args.skip + 1) != 0:
                continue
            detections, _ = detector.infer(frame.color_bgr)
            target = detector.select_target(
                detections, frame.color_bgr.shape, target_class, confidence, strategy
            )
            if target is None:
                bbox_history.clear()
                depth_history.clear()
                continue
            bbox_history.append(target)
            stable = stable_bbox(
                list(bbox_history), grasp_config.max_center_jitter_px,
                grasp_config.stable_frames,
            )
            if stable is None:
                continue
            depth = median_depth_in_bbox(
                frame.depth_m, stable, inner_ratio=grasp_config.depth_roi_inner_ratio
            )
            if depth is None:
                depth_history.clear()
                continue
            depth_history.append(float(depth))
            if len(depth_history) < grasp_config.depth_stable_frames:
                continue
            if max(depth_history) - min(depth_history) > grasp_config.max_depth_jitter_m:
                continue
            stable_depth = float(np.median(np.asarray(depth_history, dtype=float)))
            debug = fixed_view_target_debug(
                stable.center,
                stable_depth,
                frame.intrinsics_for_detection,
                matrix,
                object_geometry,
            )
            report = build_validation_report(debug, grasp_config, kinematics, calibration)
            report["kinematics_calibrated"] = bool(kinematics_mapping["calibrated"])
            encoded = json.dumps(report, ensure_ascii=False)
            print("FIXED_VIEW_TARGET " + encoded)
            if output_handle is not None:
                output_handle.write(encoded + "\n")
                output_handle.flush()
            result_count += 1
            bbox_history.clear()
            depth_history.clear()
            if result_count >= args.max_results:
                break
    finally:
        if output_handle is not None:
            output_handle.close()
        try:
            source.stop()
        except Exception:
            pass
        detector.close()

    if result_count == 0:
        print("NO_STABLE_FIXED_VIEW_TARGET", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
