#!/usr/bin/env python3
"""Pure-Python D435 + RKNN YOLO + IK grasp runtime, without ROS."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import time

import numpy as np

try:
    import cv2
except ImportError:  # Keep --help and static config checks available on dev PCs.
    cv2 = None

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.arm_motion import ArmMotion
from arm_grasp_pipeline.geometry import HandEye, euler_xyz_to_matrix, validate_rigid_transform
from arm_grasp_pipeline.grasp_state_machine import GraspConfig, GraspStateMachine
from arm_grasp_pipeline.official_kinematics import OfficialArmKinematics
from arm_grasp_pipeline.realsense_source import D435Source
from arm_grasp_pipeline.serial_servo_adapter import SerialServoArmAdapter
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
    parser.add_argument("--hand_eye_calibrated", action="store_true")
    parser.add_argument("--tool_frame_calibrated", action="store_true")
    parser.add_argument("--joint_pwm_calibrated", action="store_true")
    parser.add_argument("--serial_port", default="")
    parser.add_argument("--baudrate", type=int, default=0)
    parser.add_argument("--current_pwms", default="", help="six comma-separated live servo PWM values")
    parser.add_argument("--auto_center", action="store_true", help="allow bounded Servo000/003 visual centering")
    parser.add_argument("--center_max_commands", type=int, default=60)
    return parser.parse_args()


def load_config(path: str):
    with Path(path).expanduser().open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dataclass_kwargs(mapping, names):
    return {name: mapping[name] for name in names if name in mapping}


def parse_pwms(text):
    values = [int(part.strip()) for part in str(text).split(",") if part.strip()]
    if len(values) != 6 or any(value < 500 or value > 2500 for value in values):
        raise ValueError("current PWM reference must contain six values in 500..2500")
    return values


def draw_depth(depth_m: np.ndarray) -> np.ndarray:
    valid = np.isfinite(depth_m) & (depth_m > 0.0)
    gray = np.zeros(depth_m.shape, dtype=np.uint8)
    if np.any(valid):
        lo, hi = np.percentile(depth_m[valid], [5, 95])
        gray[valid] = np.clip(
            (depth_m[valid] - lo) / max(float(hi - lo), 1e-6) * 255.0,
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
        cv2.putText(color, "{} {:.2f}".format(box.cls, box.score),
                    (box.x1, max(20, box.y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
    if target is not None:
        cx, cy = [int(round(value)) for value in target.center]
        cv2.circle(color, (cx, cy), 6, (0, 0, 255), -1)
    status_y = color.shape[0] - 12
    cv2.rectangle(color, (0, color.shape[0] - 38), (color.shape[1], color.shape[0]), (0, 0, 0), -1)
    cv2.putText(color, "state={} infer={:.1f}ms".format(state, infer_ms),
                (10, status_y), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 255, 0), 2)
    depth = draw_depth(depth_m)
    return np.concatenate([color, depth], axis=1)


def plan_as_json(machine):
    rows = []
    for state, xyz, gripper, duration_ms in machine.plan_locked_grasp():
        ik = machine.arm.kin.inverse_pose(xyz, pitch_deg=machine.cfg.pitch_deg, gripper=0.0)
        if state.name == "CLOSE":
            command = machine.arm.adapter.pack_partial_pwm_command({5: gripper}, duration_ms)
        else:
            command = machine.arm.pack_ik_command(ik, duration_ms, include_gripper=False)
        servo_pwms = None if getattr(ik, "servo_pwms", None) is None else list(ik.servo_pwms)
        rows.append({
            "state": state.name,
            "xyz_m": [float(value) for value in xyz],
            "gripper": float(gripper),
            "duration_ms": int(duration_ms),
            "joints_rad": [float(value) for value in ik.joints_rad],
            "arm_servo_pwms_000_003": servo_pwms,
            "gripper_pwm_005": int(gripper),
            "command": command,
        })
    return rows


def main() -> int:
    args = parse_args()
    if args.skip < 0 or args.max_frames < 0:
        raise ValueError("--skip and --max_frames must be non-negative")
    if not args.dry_run:
        if not args.enable_arm:
            raise ValueError("real output requires --enable_arm")
        if not args.auto_center and not args.execute_on_lock:
            raise ValueError("real output must enable bounded centering or execute a calibrated grasp")
        if args.execute_on_lock and not args.hand_eye_calibrated:
            raise ValueError("real grasp is blocked until --hand_eye_calibrated is explicitly provided")
        if args.execute_on_lock and not args.tool_frame_calibrated:
            raise ValueError("real grasp is blocked until --tool_frame_calibrated is explicitly provided")
        if args.execute_on_lock and not args.joint_pwm_calibrated:
            raise ValueError("real grasp is blocked until --joint_pwm_calibrated is explicitly provided")
        if args.execute_on_lock and args.auto_center:
            raise ValueError("real grasp and auto-centering cannot run together until dynamic FK is calibrated")

    config = load_config(args.config)
    serial_cfg = dict(config.get("serial", {}))
    runtime_cfg = dict(config.get("runtime", {}))
    grasp_cfg = dict(config.get("grasp", {}))
    hand_eye_cfg = dict(config.get("hand_eye", {}))
    realsense_cfg = dict(config.get("realsense", {}))
    kinematics_cfg = dict(config.get("kinematics", {}))
    tool_reference_cfg = dict(config.get("tool_reference", {}))
    camera_mount_cfg = dict(config.get("camera_mount", {}))
    centering_cfg = dict(config.get("visual_centering", {}))

    if not args.dry_run and args.execute_on_lock and not bool(hand_eye_cfg.get("calibrated", False)):
        raise ValueError("config hand_eye.calibrated is false; refusing real grasp")
    if not args.dry_run and args.execute_on_lock and not bool(tool_reference_cfg.get("calibrated", False)):
        raise ValueError("config tool_reference.calibrated is false; refusing real grasp")
    if not args.dry_run and args.execute_on_lock:
        if not bool(camera_mount_cfg.get("frozen", False)):
            raise ValueError("camera mount relation is not frozen; refusing real grasp")
        if not bool(camera_mount_cfg.get("requires_fixed_servo004", False)):
            raise ValueError("current camera/TCP model requires Servo004 to be fixed")
        if int(camera_mount_cfg.get("fixed_servo004_pwm", -1)) != int(grasp_cfg.get("wrist_fixed_pwm", -2)):
            raise ValueError("camera mount and grasp config disagree on the fixed Servo004 PWM")
        if list(tool_reference_cfg.get("at_servo_pwms", [])) != list(grasp_cfg.get("retry_pose_pwms", [])):
            raise ValueError("tool reference and retry pose PWM values must match")
    if not args.dry_run and args.execute_on_lock and not bool(serial_cfg.get("joint_pwm_calibrated", False)):
        raise ValueError("config serial.joint_pwm_calibrated is false; refusing real grasp")

    target_class = args.target_class or runtime_cfg.get("target_class", "bottle")
    confidence = args.conf if args.conf is not None else float(runtime_cfg.get("confidence", 0.25))
    strategy = args.strategy or runtime_cfg.get("selection_strategy", "nearest_center")
    adapter = SerialServoArmAdapter(
        port=args.serial_port or serial_cfg.get("port", "/dev/ttyUSB0"),
        baudrate=args.baudrate or int(serial_cfg.get("baudrate", 115200)),
        dry_run=args.dry_run,
    )
    backend = str(kinematics_cfg.get("backend", "official_f103"))
    if backend == "official_f103":
        kin = OfficialArmKinematics(
            l0_m=float(kinematics_cfg.get("l0_m", 0.100)),
            l1_m=float(kinematics_cfg.get("l1_m", 0.105)),
            l2_m=float(kinematics_cfg.get("l2_m", 0.088)),
            l3_m=float(kinematics_cfg.get("l3_m", 0.155)),
        )
        calibrated_reference_pwms = list(tool_reference_cfg.get(
            "at_servo_pwms",
            grasp_cfg.get("retry_pose_pwms", [1380, 1909, 1900, 620, 1500, 1500]),
        ))
        reference_pwms = parse_pwms(args.current_pwms) if args.current_pwms else calibrated_reference_pwms
        if bool(tool_reference_cfg.get("calibrated", False)):
            if list(reference_pwms) != calibrated_reference_pwms:
                raise ValueError("calibrated T_base_tool is valid only at tool_reference.at_servo_pwms")
            matrix_4x4 = tool_reference_cfg.get("base_to_tool_matrix_4x4")
            if matrix_4x4 is not None:
                reference_matrix = validate_rigid_transform(matrix_4x4, "T_base_tool_reference")
            else:
                reference_matrix = euler_xyz_to_matrix(
                    tool_reference_cfg["base_to_tool_xyz_m"],
                    tool_reference_cfg["base_to_tool_rpy_deg"],
                )
        else:
            # The vendor code has no forward kinematics or TCP definition.
            # This estimate exists only to keep dry-run diagnostics available.
            reference_matrix = kin.estimate_tool_matrix_from_pwm(reference_pwms)
        arm = ArmMotion(adapter, kinematics=kin, reference_tool_matrix=reference_matrix)
    else:
        raise ValueError("unsupported kinematics backend: {}".format(backend))
    center_names = set(CenteringConfig.__dataclass_fields__.keys())
    centerer = PWMVisualCentering(CenteringConfig(**dataclass_kwargs(centering_cfg, center_names)))
    center_duration_ms = int(centering_cfg.get("duration_ms", 180))
    center_interval_s = float(centering_cfg.get("interval_s", 0.22))
    current_pwms = list(reference_pwms)
    center_command_count = 0
    last_center_command_time = 0.0
    grasp_names = set(GraspConfig.__dataclass_fields__.keys())
    machine_cfg = GraspConfig(**dataclass_kwargs(grasp_cfg, grasp_names))
    hand_names = {"x", "y", "z", "roll_deg", "pitch_deg", "yaw_deg", "matrix_4x4"}
    hand_eye = HandEye(**dataclass_kwargs(hand_eye_cfg, hand_names))
    geometry_calibrated = bool(
        hand_eye_cfg.get("calibrated", False) and tool_reference_cfg.get("calibrated", False)
    )

    if cv2 is None:
        raise RuntimeError("opencv-python is required to run the D435 YOLO grasp pipeline")
    from arm_grasp_pipeline.rknn_yolo_detector import RknnYolo11Detector

    detector = RknnYolo11Detector(
        args.model_path,
        args.yolo_dir,
        target=args.target,
        device_id=args.device_id,
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

    try:
        detector.start()
        source.start()
        if not args.dry_run:
            adapter.connect()
            if args.execute_on_lock:
                if backend != "official_f103":
                    raise ValueError("real grasp currently requires the official_f103 backend")
                prepare_ms = int(grasp_cfg.get("retry_motion_ms", 3500))
                payload = adapter.send_pwm_command(reference_pwms, prepare_ms)
                time.sleep(prepare_ms / 1000.0 + float(grasp_cfg.get("motion_settle_s", 0.15)))
                print("REFERENCE_POSE_READY " + json.dumps({
                    "pwms": reference_pwms,
                    "payload": payload,
                    "servo004_fixed_pwm": int(grasp_cfg.get("wrist_fixed_pwm", 1500)),
                }, ensure_ascii=False))
        if metrics_path is not None:
            metrics_path.parent.mkdir(parents=True, exist_ok=True)
            metrics_handle = metrics_path.open("w", encoding="utf-8")

        while args.max_frames <= 0 or frame_count < args.max_frames:
            frame = source.read()
            frame_count += 1
            if machine is None:
                machine = GraspStateMachine(
                    arm,
                    frame.intrinsics_for_detection,
                    cfg=machine_cfg,
                    hand_eye=hand_eye,
                )

            if (frame_count - 1) % (args.skip + 1) == 0:
                detections, infer_ms = detector.infer(frame.color_bgr)
                inference_count += 1
                selected = detector.select_target(
                    detections,
                    frame.color_bgr.shape,
                    target_class,
                    confidence,
                    strategy,
                )
                machine.update_detection(selected)
                target = None
                if selected is not None and args.auto_center and current_pwms is not None:
                    updates = centerer.command(selected, frame.color_bgr.shape, current_pwms)
                    now = time.monotonic()
                    if updates and now - last_center_command_time >= center_interval_s:
                        if center_command_count >= args.center_max_commands:
                            raise RuntimeError("visual centering command limit reached")
                        payload = adapter.send_partial_pwm_command(updates, center_duration_ms)
                        for servo_id, pwm in updates.items():
                            current_pwms[servo_id] = pwm
                        arm.set_reference_tool_matrix(kin.estimate_tool_matrix_from_pwm(current_pwms))
                        center_command_count += 1
                        last_center_command_time = now
                        machine.update_detection(None)
                        print("CENTER_CMD " + json.dumps({
                            "count": center_command_count,
                            "updates": updates,
                            "current_pwms": current_pwms,
                            "payload": payload,
                        }, ensure_ascii=False))
                    elif not updates:
                        target = machine.try_lock_depth(frame.depth_m)
                elif selected is not None:
                    target = machine.try_lock_depth(frame.depth_m)
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
                    "state": machine.state.name,
                    "infer_ms": infer_ms,
                }
                if metrics_handle is not None:
                    metrics_handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                    metrics_handle.flush()
                if frame_count == 1 or frame_count % 15 == 0:
                    print(json.dumps(row, ensure_ascii=False))
                if target is not None:
                    locked = True
                    lock_debug = machine.last_lock_debug
                    lock_record = {
                        "target_base_m": [float(value) for value in target],
                        "geometry_calibrated": geometry_calibrated,
                        "pixel_xy": None if lock_debug is None else list(lock_debug.pixel_xy),
                        "depth_m": None if lock_debug is None else float(lock_debug.depth_m),
                        "point_camera_m": None if lock_debug is None else list(lock_debug.point_camera_m),
                        "point_tool_m": None if lock_debug is None else list(lock_debug.point_tool_m),
                    }
                    print("GRASP_LOCK " + json.dumps(lock_record, ensure_ascii=False))
                    if not geometry_calibrated:
                        plan = None
                        print("GRASP_PLAN_BLOCKED " + json.dumps({
                            "reason": "hand-eye and tool reference are not calibrated",
                            "camera_point_m": lock_record["point_camera_m"],
                        }, ensure_ascii=False))
                    else:
                        try:
                            plan = plan_as_json(machine)
                        except ValueError as exc:
                            plan = None
                            print("GRASP_PLAN_REJECTED " + json.dumps({"reason": str(exc)}, ensure_ascii=False))
                    if plan is not None:
                        print("GRASP_PLAN " + json.dumps(plan, ensure_ascii=False))
                        if args.execute_on_lock:
                            ok = machine.execute_locked_grasp()
                            print("GRASP_EXECUTE {} dry_run={}".format(ok, args.dry_run))
                    if args.stop_on_lock:
                        last_visual = draw_overlay(
                            frame.color_bgr, frame.depth_m, detections, selected, machine.state.name, infer_ms)
                        break

            last_visual = draw_overlay(
                frame.color_bgr, frame.depth_m, detections, selected,
                machine.state.name if machine is not None else "START", infer_ms,
            )
            if not args.no_show:
                cv2.imshow("D435 YOLO Grasp", last_visual)
                if cv2.waitKey(1) & 0xFF in (27, ord("q")):
                    break
    finally:
        if metrics_handle is not None:
            metrics_handle.close()
        if output_dir is not None and last_visual is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output_dir / "last_rgbd_grasp.png"), last_visual)
        if not args.dry_run:
            try:
                adapter.stop()
            except Exception as exc:
                print("arm stop warning: {}".format(exc), file=sys.stderr)
        adapter.close()
        try:
            source.stop()
        except Exception:
            pass
        detector.close()
        cv2.destroyAllWindows()

    print("SUMMARY frames={} inferences={} locked={} center_commands={} dry_run={} hand_eye_calibrated={} tool_frame_calibrated={} geometry_calibrated={}".format(
        frame_count, inference_count, locked, center_command_count,
        args.dry_run, bool(hand_eye_cfg.get("calibrated", False)),
        bool(tool_reference_cfg.get("calibrated", False)), geometry_calibrated))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
