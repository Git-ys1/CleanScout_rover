#!/usr/bin/env python3
"""Fixed-observation D435 + RKNN YOLO grasp runtime, without ROS."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

import numpy as np

try:
    import cv2
except ImportError:  # Keep --help and config gates usable on development PCs.
    cv2 = None

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.arm_motion import ArmMotion
from arm_grasp_pipeline.fixed_view import (
    REQUIRED_WRIST_PWM,
    FixedViewCalibration,
    ObjectGeometry,
)
from arm_grasp_pipeline.geometry import depth_pixel_to_camera
from arm_grasp_pipeline.grasp_planner import GraspConfig, GraspState, validate_servo_pwms
from arm_grasp_pipeline.grasp_state_machine import GraspStateMachine
from arm_grasp_pipeline.official_kinematics import OfficialArmKinematics
from arm_grasp_pipeline.realsense_source import D435Source
from arm_grasp_pipeline.serial_servo_adapter import SerialServoArmAdapter
from arm_grasp_pipeline.target_depth import median_depth_in_bbox
from arm_grasp_pipeline.visual_centering import CenteringConfig, PWMVisualCentering


DEFAULT_CONFIG = ROOT / "config/arm_grasp_default.json"
DEFAULT_YOLO_DIR = Path.home() / "rk3588_ai/rknn_model_zoo/examples/yolo11/python"


def str2bool(value):
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in ("1", "true", "yes", "y", "on"):
        return True
    if text in ("0", "false", "no", "n", "off"):
        return False
    raise argparse.ArgumentTypeError("expected true/false")


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
    parser.add_argument("--max_frames", type=int, default=0)
    parser.add_argument("--skip", type=int, default=0)
    parser.add_argument("--no_show", action="store_true")
    parser.add_argument("--save_dir", default="")
    parser.add_argument("--metrics_path", default="")
    parser.add_argument("--execute_on_lock", type=str2bool, default=False)
    parser.add_argument("--stop_on_lock", type=str2bool, default=True)
    parser.add_argument("--dry_run", type=str2bool, default=True)
    parser.add_argument("--enable_arm", action="store_true")
    parser.add_argument("--joint_pwm_calibrated", action="store_true")
    parser.add_argument(
        "--max_stage", choices=("open", "pre_grasp", "approach", "close", "lift"),
        default="lift",
    )
    parser.add_argument("--serial_port", default="")
    parser.add_argument("--baudrate", type=int, default=0)
    parser.add_argument("--current_pwms", default="",
                        help="six live PWM values; only valid for centering-only mode")
    parser.add_argument("--auto_center", action="store_true",
                        help="bounded centering only; incompatible with fixed-view grasp")
    parser.add_argument("--center_max_commands", type=int, default=60)
    return parser.parse_args()


def load_config(path):
    with Path(path).expanduser().open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dataclass_kwargs(mapping, names):
    return {name: mapping[name] for name in names if name in mapping}


def parse_pwms(text):
    values = [int(part.strip()) for part in str(text).split(",") if part.strip()]
    if len(values) != 6 or any(value < 500 or value > 2490 for value in values):
        raise ValueError("current PWM reference must contain six values in 500..2490")
    return values


def reference_pose_mismatches(reference_pwms, actual_by_id, tolerance_pwm,
                              servo_ids=None):
    tolerance = int(tolerance_pwm)
    if tolerance < 0:
        raise ValueError("reference pose tolerance must be non-negative")
    mismatches = {}
    ids = range(len(reference_pwms)) if servo_ids is None else servo_ids
    for servo_id in (int(value) for value in ids):
        target = reference_pwms[servo_id]
        actual = actual_by_id.get(servo_id)
        if actual is None or abs(int(actual) - int(target)) > tolerance:
            mismatches[str(servo_id)] = {
                "target_pwm": int(target),
                "actual_pwm": None if actual is None else int(actual),
                "delta_pwm": None if actual is None else abs(int(actual) - int(target)),
            }
    return mismatches


def expected_stage_pwms(plan_rows, max_stage):
    stage = str(max_stage).strip().upper()
    matches = [row for row in plan_rows if str(row.get("state", "")).upper() == stage]
    if not matches:
        raise ValueError("grasp plan has no {} stage".format(stage))
    values = [int(value) for value in matches[-1]["servo_pwms_000_005"]]
    if len(values) != 6:
        raise ValueError("stage PWM record must contain six values")
    return values


def validate_real_grasp_request(args, config, calibration: FixedViewCalibration):
    """Reject unsafe real output before any serial port is opened."""
    if args.dry_run or not args.execute_on_lock:
        return
    if not args.enable_arm:
        raise ValueError("real output requires --enable_arm")
    if args.auto_center:
        raise ValueError(
            "real fixed-view grasp and auto_center cannot run together without calibrated dynamic FK"
        )
    calibration.require_real_grasp_ready(required_wrist_pwm=REQUIRED_WRIST_PWM)

    serial_cfg = dict(config.get("serial", {}))
    grasp_cfg = dict(config.get("grasp", {}))
    camera_mount = dict(config.get("camera_mount", {}))
    kinematics_cfg = dict(config.get("kinematics", {}))
    joint_cfg = dict(config.get("joint_pwm_calibration", {}))
    if not args.joint_pwm_calibrated:
        raise ValueError("real grasp requires explicit --joint_pwm_calibrated")
    if not bool(serial_cfg.get("joint_pwm_calibrated", False)):
        raise ValueError("config serial.joint_pwm_calibrated is false")
    if not bool(kinematics_cfg.get("calibrated", False)):
        raise ValueError("config kinematics.calibrated is false")
    if not bool(joint_cfg.get("calibrated", False)):
        raise ValueError("config joint_pwm_calibration.calibrated is false")
    # Construction validates range, scale, zero count and per-axis signs.
    OfficialArmKinematics.from_config(kinematics_cfg, joint_cfg)
    if not bool(camera_mount.get("frozen", False)):
        raise ValueError("camera mount relation is not frozen")
    if not bool(camera_mount.get("requires_fixed_servo004", False)):
        raise ValueError("fixed-view camera model must require fixed Servo004")
    if int(camera_mount.get("fixed_servo004_pwm", -1)) != REQUIRED_WRIST_PWM:
        raise ValueError("camera mount Servo004 PWM must be {}".format(REQUIRED_WRIST_PWM))
    if int(grasp_cfg.get("wrist_fixed_pwm", -1)) != REQUIRED_WRIST_PWM:
        raise ValueError("grasp Servo004 PWM must be {}".format(REQUIRED_WRIST_PWM))
    if list(grasp_cfg.get("retry_pose_pwms", [])) != list(calibration.reference_servo_pwms):
        raise ValueError("grasp reference pose must equal fixed-view calibration pose")
    if args.current_pwms and parse_pwms(args.current_pwms) != list(calibration.reference_servo_pwms):
        raise ValueError("real fixed-view grasp cannot override the calibrated reference pose")


def draw_depth(depth_m):
    valid = np.isfinite(depth_m) & (depth_m > 0.0)
    gray = np.zeros(depth_m.shape, dtype=np.uint8)
    if np.any(valid):
        low, high = np.percentile(depth_m[valid], [5, 95])
        gray[valid] = np.clip(
            (depth_m[valid] - low) / max(float(high - low), 1e-6) * 255.0,
            0,
            255,
        ).astype(np.uint8)
    image = cv2.applyColorMap(gray, cv2.COLORMAP_TURBO)
    image[~valid] = 0
    return image


def draw_overlay(color_bgr, depth_m, detections, target, state, infer_ms):
    color = color_bgr.copy()
    for box in detections:
        cv2.rectangle(color, (box.x1, box.y1), (box.x2, box.y2), (255, 0, 0), 2)
        cv2.putText(
            color, "{} {:.2f}".format(box.cls, box.score),
            (box.x1, max(20, box.y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX,
            0.5, (0, 255, 255), 2,
        )
    if target is not None:
        cx, cy = [int(round(value)) for value in target.center]
        cv2.circle(color, (cx, cy), 6, (0, 0, 255), -1)
    cv2.rectangle(color, (0, color.shape[0] - 38),
                  (color.shape[1], color.shape[0]), (0, 0, 0), -1)
    cv2.putText(
        color, "state={} infer={:.1f}ms".format(state, infer_ms),
        (10, color.shape[0] - 12), cv2.FONT_HERSHEY_SIMPLEX,
        0.62, (0, 255, 0), 2,
    )
    return np.concatenate([color, draw_depth(depth_m)], axis=1)


def same_target_observation(reference_center, reference_depth_m, target, target_depth_m,
                            center_tolerance_px, depth_tolerance_m):
    if target is None or target_depth_m is None:
        return False
    dx = float(target.center[0]) - float(reference_center[0])
    dy = float(target.center[1]) - float(reference_center[1])
    return (
        float(np.hypot(dx, dy)) <= float(center_tolerance_px)
        and abs(float(target_depth_m) - float(reference_depth_m)) <= float(depth_tolerance_m)
    )


def plan_as_json(machine):
    rows = []
    for step in machine.plan_locked_grasp():
        row = step.as_dict()
        if step.state in (GraspState.OPEN, GraspState.CLOSE):
            command = machine.arm.adapter.pack_partial_pwm_command(
                {5: step.gripper_pwm}, step.duration_ms
            )
        else:
            command = machine.arm.pack_ik_command(
                step.ik, step.duration_ms, include_gripper=False
            )
        row["command"] = command
        rows.append(row)
    return rows


def main() -> int:
    args = parse_args()
    if args.skip < 0 or args.max_frames < 0:
        raise ValueError("--skip and --max_frames must be non-negative")
    if not args.dry_run:
        if not args.enable_arm:
            raise ValueError("real output requires --enable_arm")
        if not args.auto_center and not args.execute_on_lock:
            raise ValueError("real output must select centering or fixed-view grasp")
        if args.auto_center and args.execute_on_lock:
            raise ValueError("auto_center and fixed-view real grasp are mutually exclusive")

    config = load_config(args.config)
    serial_cfg = dict(config.get("serial", {}))
    runtime_cfg = dict(config.get("runtime", {}))
    grasp_cfg = dict(config.get("grasp", {}))
    realsense_cfg = dict(config.get("realsense", {}))
    kinematics_cfg = dict(config.get("kinematics", {}))
    joint_pwm_cfg = dict(config.get("joint_pwm_calibration", {}))
    centering_cfg = dict(config.get("visual_centering", {}))
    calibration = FixedViewCalibration.from_mapping(
        dict(config.get("fixed_view_calibration", {}))
    )
    object_geometry = ObjectGeometry.from_mapping(dict(config.get("object_geometry", {})))
    validate_real_grasp_request(args, config, calibration)

    matrix = None
    try:
        matrix = calibration.matrix()
    except ValueError:
        if args.execute_on_lock:
            raise ValueError(
                "fixed-view matrix is required for grasp planning; run calibrate_base_camera_3d.py"
            )

    target_class = args.target_class or runtime_cfg.get("target_class", "bottle")
    confidence = args.conf if args.conf is not None else float(runtime_cfg.get("confidence", 0.25))
    strategy = args.strategy or runtime_cfg.get("selection_strategy", "nearest_center")
    adapter = SerialServoArmAdapter(
        port=args.serial_port or serial_cfg.get("port", "/dev/ttyUSB0"),
        baudrate=args.baudrate or int(serial_cfg.get("baudrate", 115200)),
        dry_run=args.dry_run,
    )
    required_kinematics = {
        "backend", "calibrated", "l0_m", "l1_m", "l2_m", "l3_m",
    }
    missing_kinematics = sorted(required_kinematics.difference(kinematics_cfg))
    if missing_kinematics:
        raise ValueError(
            "kinematics config missing fields: " + ", ".join(missing_kinematics)
        )
    if str(kinematics_cfg["backend"]) != "official_f103":
        raise ValueError("fixed-view grasp requires the official_f103 kinematics backend")
    kinematics = OfficialArmKinematics.from_config(kinematics_cfg, joint_pwm_cfg)
    arm = ArmMotion(adapter, kinematics=kinematics)
    reference_pwms = list(calibration.reference_servo_pwms)
    current_pwms = parse_pwms(args.current_pwms) if args.current_pwms else list(reference_pwms)

    machine_cfg = GraspConfig.from_mapping(grasp_cfg)
    if list(machine_cfg.retry_pose_pwms) != reference_pwms:
        raise ValueError("grasp retry pose and fixed-view reference pose must match")
    if machine_cfg.wrist_fixed_pwm != REQUIRED_WRIST_PWM:
        raise ValueError("Servo004 must be fixed at PWM {}".format(REQUIRED_WRIST_PWM))
    validate_servo_pwms(reference_pwms, machine_cfg)

    center_names = set(CenteringConfig.__dataclass_fields__.keys())
    centerer = PWMVisualCentering(
        CenteringConfig(**dataclass_kwargs(centering_cfg, center_names))
    )
    center_duration_ms = int(centering_cfg.get("duration_ms", 180))
    center_interval_s = float(centering_cfg.get("interval_s", 0.22))
    center_command_count = 0
    last_center_command_time = 0.0

    if cv2 is None:
        raise RuntimeError("opencv-python is required to run the D435 YOLO grasp pipeline")
    from arm_grasp_pipeline.rknn_yolo_detector import RknnYolo11Detector

    detector = RknnYolo11Detector(
        args.model_path, args.yolo_dir, target=args.target, device_id=args.device_id,
        object_threshold=confidence,
    )
    source = D435Source(
        int(realsense_cfg.get("width", 640)),
        int(realsense_cfg.get("height", 480)),
        int(realsense_cfg.get("fps", 30)),
        serial_number=realsense_cfg.get("serial_number") or None,
    )
    output_dir = Path(args.save_dir).expanduser() if args.save_dir else None
    metrics_path = Path(args.metrics_path).expanduser() if args.metrics_path else None
    metrics_handle = None
    machine = None
    last_visual = None
    frame_count = 0
    inference_count = 0
    selected = None
    detections = []
    infer_ms = 0.0
    locked = False
    grasp_result = "not_executed"

    try:
        detector.start()
        source.start()
        if not args.dry_run:
            adapter.connect()
            if args.execute_on_lock:
                prepare_ms = int(grasp_cfg.get("retry_motion_ms", 3500))
                payload = adapter.send_pwm_command(reference_pwms, prepare_ms)
                time.sleep(prepare_ms / 1000.0 + float(grasp_cfg.get("motion_settle_s", 0.15)))
                actual_pwms = adapter.read_pwms(range(6), timeout_s=0.8)
                pose_tolerance = int(serial_cfg.get("reference_pose_tolerance_pwm", 40))
                mismatches = reference_pose_mismatches(
                    reference_pwms, actual_pwms, pose_tolerance
                )
                if mismatches:
                    raise RuntimeError(
                        "fixed-view reference pose readback failed: "
                        + json.dumps(mismatches, ensure_ascii=False)
                    )
                print("REFERENCE_POSE_READY " + json.dumps({
                    "pwms": reference_pwms,
                    "readback_pwms": actual_pwms,
                    "tolerance_pwm": pose_tolerance,
                    "payload": payload,
                    "T_base_camera_reference_valid": True,
                }, ensure_ascii=False))
        if metrics_path is not None:
            metrics_path.parent.mkdir(parents=True, exist_ok=True)
            metrics_handle = metrics_path.open("w", encoding="utf-8")

        while args.max_frames <= 0 or frame_count < args.max_frames:
            frame = source.read()
            frame_count += 1
            if machine is None and matrix is not None:
                machine = GraspStateMachine(
                    arm,
                    frame.intrinsics_for_detection,
                    matrix,
                    cfg=machine_cfg,
                    object_geometry=object_geometry,
                )

            if (frame_count - 1) % (args.skip + 1) == 0:
                detections, infer_ms = detector.infer(frame.color_bgr)
                inference_count += 1
                selected = detector.select_target(
                    detections, frame.color_bgr.shape, target_class, confidence, strategy
                )
                target = None
                if machine is not None:
                    machine.update_detection(selected)
                if selected is not None and args.auto_center:
                    updates = centerer.command(selected, frame.color_bgr.shape, current_pwms)
                    now = time.monotonic()
                    if updates and now - last_center_command_time >= center_interval_s:
                        if center_command_count >= args.center_max_commands:
                            raise RuntimeError("visual centering command limit reached")
                        payload = adapter.send_partial_pwm_command(updates, center_duration_ms)
                        for servo_id, pwm in updates.items():
                            current_pwms[servo_id] = pwm
                        center_command_count += 1
                        last_center_command_time = now
                        if machine is not None:
                            machine.update_detection(None)
                        print("CENTER_ONLY_CMD " + json.dumps({
                            "count": center_command_count,
                            "updates": updates,
                            "current_pwms": current_pwms,
                            "payload": payload,
                            "grasp_disabled": True,
                        }, ensure_ascii=False))
                    elif not updates and machine is not None:
                        target = machine.try_lock_depth(frame.depth_m)
                elif selected is not None and machine is not None:
                    target = machine.try_lock_depth(frame.depth_m)
                elif selected is not None and matrix is None:
                    depth = median_depth_in_bbox(frame.depth_m, selected)
                    if depth is not None:
                        camera_point = depth_pixel_to_camera(
                            selected.center, depth, frame.intrinsics_for_detection
                        )
                        print("FIXED_VIEW_PLAN_BLOCKED " + json.dumps({
                            "reason": "base_to_camera_matrix_4x4 is not configured",
                            "pixel_xy": list(selected.center),
                            "depth_m": float(depth),
                            "point_camera_m": camera_point.tolist(),
                        }, ensure_ascii=False))

                row = {
                    "time": time.time(),
                    "frame": frame_count,
                    "inference": inference_count,
                    "detections": len(detections),
                    "target": None if selected is None else {
                        "class": selected.cls,
                        "score": selected.score,
                        "box": [selected.x1, selected.y1, selected.x2, selected.y2],
                        "center": list(selected.center),
                    },
                    "state": "UNCALIBRATED" if machine is None else machine.state.name,
                    "infer_ms": infer_ms,
                }
                if metrics_handle is not None:
                    metrics_handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                    metrics_handle.flush()
                if frame_count == 1 or frame_count % 15 == 0:
                    print(json.dumps(row, ensure_ascii=False))

                if target is not None:
                    locked = True
                    debug = machine.last_lock_debug
                    lock_record = {
                        "pixel_xy": list(debug.pixel_xy),
                        "depth_m": float(debug.depth_m),
                        "point_camera_m": list(debug.point_camera_m),
                        "point_base_surface_m": list(debug.point_base_surface_m),
                        "bottle_center_base_m": list(debug.bottle_center_base_m),
                        "approach_axis_base": list(debug.approach_axis_base),
                    }
                    print("GRASP_LOCK " + json.dumps(lock_record, ensure_ascii=False))
                    try:
                        plan = plan_as_json(machine)
                    except ValueError as exc:
                        print("GRASP_PLAN_REJECTED " + json.dumps(
                            {"reason": str(exc)}, ensure_ascii=False
                        ))
                        grasp_result = "plan_rejected"
                        plan = None
                    if plan is not None:
                        print("GRASP_PLAN " + json.dumps(plan, ensure_ascii=False))
                        if args.execute_on_lock:
                            ok = machine.execute_locked_grasp(max_stage=args.max_stage)
                            grasp_result = "stage_complete" if ok else "motion_failed"
                            print("GRASP_EXECUTE {} dry_run={} max_stage={}".format(
                                ok, args.dry_run, args.max_stage
                            ))
                            if ok and not args.dry_run:
                                expected_pwms = expected_stage_pwms(plan, args.max_stage)
                                actual_pwms = adapter.read_pwms(range(6), timeout_s=0.8)
                                pose_tolerance = int(
                                    serial_cfg.get("reference_pose_tolerance_pwm", 40)
                                )
                                arm_mismatches = reference_pose_mismatches(
                                    expected_pwms,
                                    actual_pwms,
                                    pose_tolerance,
                                    servo_ids=range(5),
                                )
                                gripper_actual = actual_pwms.get(5)
                                readback = {
                                    "stage": str(args.max_stage).upper(),
                                    "expected_pwms": expected_pwms,
                                    "actual_pwms": actual_pwms,
                                    "arm_tolerance_pwm": pose_tolerance,
                                    "arm_mismatches_000_004": arm_mismatches,
                                    "gripper_target_pwm": expected_pwms[5],
                                    "gripper_actual_pwm": gripper_actual,
                                    "gripper_delta_pwm": (
                                        None if gripper_actual is None
                                        else abs(int(gripper_actual) - expected_pwms[5])
                                    ),
                                }
                                print("STAGE_READBACK " + json.dumps(
                                    readback, ensure_ascii=False
                                ))
                                if arm_mismatches:
                                    grasp_result = "stage_readback_failed"
                                    raise RuntimeError(
                                        "stage arm readback failed: "
                                        + json.dumps(arm_mismatches, ensure_ascii=False)
                                    )
                    if args.stop_on_lock:
                        break

            state = "UNCALIBRATED" if machine is None else machine.state.name
            last_visual = draw_overlay(
                frame.color_bgr, frame.depth_m, detections, selected, state, infer_ms
            )
            if not args.no_show:
                cv2.imshow("D435 Fixed-View Grasp", last_visual)
                if cv2.waitKey(1) & 0xFF in (27, ord("q")):
                    break
    finally:
        if metrics_handle is not None:
            metrics_handle.close()
        if output_dir is not None and last_visual is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output_dir / "last_fixed_view_grasp.png"), last_visual)
        if not args.dry_run:
            # PDST releases the holding state on this heavy arm and lets the
            # mechanism sag under gravity. A completed or rejected staged run
            # must hold its last commanded pose for physical inspection.
            print("ARM_HOLD_LAST_POSE automatic_PDST=false")
        adapter.close()
        try:
            source.stop()
        except Exception:
            pass
        detector.close()
        cv2.destroyAllWindows()

    print("SUMMARY frames={} inferences={} locked={} center_commands={} grasp_result={} dry_run={} fixed_view_calibrated={}".format(
        frame_count, inference_count, locked, center_command_count,
        grasp_result, args.dry_run, calibration.calibrated,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
