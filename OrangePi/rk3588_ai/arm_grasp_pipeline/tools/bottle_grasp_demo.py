#!/usr/bin/env python3
"""One-button bottle demo: table view, visual centering, grasp and lift."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.arm_motion import ArmMotion
from arm_grasp_pipeline.bottle_demo import (
    BottleDemoConfig,
    BottleDemoVision,
    BottleGraspDemo,
    FarTargetLock,
)
from arm_grasp_pipeline.geometry import FrameTransforms
from arm_grasp_pipeline.grasp_state_machine import JsonlGraspLogger
from arm_grasp_pipeline.official_kinematics import OfficialArmKinematics
from arm_grasp_pipeline.realsense_source import D435Source
from arm_grasp_pipeline.serial_servo_adapter import SerialServoArmAdapter
from arm_grasp_pipeline.target_depth import BBox


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


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--model_path", default="~/rk3588_ai/models/official_yolo11.rknn")
    parser.add_argument("--yolo_dir", default=str(DEFAULT_YOLO_DIR))
    parser.add_argument("--target", default="rk3588")
    parser.add_argument("--device_id", default=None)
    parser.add_argument("--conf", type=float, default=None)
    parser.add_argument("--serial_port", default="")
    parser.add_argument("--baudrate", type=int, default=0)
    parser.add_argument("--dry_run", type=str2bool, default=True)
    parser.add_argument("--enable_arm", action="store_true")
    parser.add_argument("--full_lift", type=str2bool, default=None)
    parser.add_argument(
        "--max_stage",
        choices=("center", "pregrasp", "approach", "lift"),
        default="lift",
        help="approach stops with the gripper open; lift runs close/verify/lift",
    )
    parser.add_argument(
        "--allow_missing_gripper_prad",
        type=str2bool,
        default=False,
        help="approach-only emergency: Servo005 may be missing while Servo000..004 remain strict",
    )
    parser.add_argument(
        "--checkpoint_path",
        default="~/rk3588_ai/debug_logs/bottle_demo_latest_lock.json",
    )
    parser.add_argument("--resume_lock", default="")
    parser.add_argument("--resume_lock_max_age_s", type=float, default=300.0)
    parser.add_argument("--save_dir", default="")
    parser.add_argument("--check_config", action="store_true")
    parser.add_argument("--no_show", action="store_true", help="accepted for command compatibility; demo is headless")
    return parser.parse_args(argv)


def load_config(path):
    with Path(path).expanduser().open("r", encoding="utf-8") as handle:
        return json.load(handle)


def require_real_calibration(config, frames):
    failures = []
    if not frames.hand_eye_calibrated:
        failures.append("hand_eye.calibrated=false")
    if not bool(config.get("hand_eye", {}).get("dynamic_validation", {}).get("accepted", False)):
        failures.append("hand_eye.dynamic_validation.accepted=false")
    if not frames.closed_calibrated:
        failures.append("closed TCP calibrated=false")
    if not bool(config.get("kinematics", {}).get("calibrated", False)):
        failures.append("kinematics.calibrated=false")
    if not bool(config.get("joint_pwm_calibration", {}).get("calibrated", False)):
        failures.append("joint_pwm_calibration.calibrated=false")
    if not bool(config.get("serial", {}).get("joint_pwm_calibrated", False)):
        failures.append("serial.joint_pwm_calibrated=false")
    if int(config.get("grasp", {}).get("wrist_fixed_pwm", -1)) != 1500:
        failures.append("grasp.wrist_fixed_pwm!=1500")
    if failures:
        raise ValueError("real demo calibration gate: " + "; ".join(failures))


def main(argv=None):
    args = parse_args(argv)
    config = load_config(args.config)
    if args.full_lift is not None:
        config["demo_grasp"]["full_lift_enabled"] = bool(args.full_lift)
    if args.allow_missing_gripper_prad and args.max_stage not in (
        "center", "pregrasp", "approach"
    ):
        raise ValueError(
            "--allow_missing_gripper_prad true requires an open-gripper max stage"
        )
    if args.resume_lock and args.max_stage != "approach":
        raise ValueError("--resume_lock requires --max_stage approach")
    demo_cfg = BottleDemoConfig.from_mapping(config["demo_grasp"])
    frames = FrameTransforms.from_config(config, require_calibrated=True)
    kinematics = OfficialArmKinematics.from_config(
        config["kinematics"], config["joint_pwm_calibration"]
    )
    require_real_calibration(config, frames)
    if not args.dry_run and not args.enable_arm:
        raise ValueError("real demo requires explicit --enable_arm")

    print("BOTTLE_DEMO_CONFIG " + json.dumps({
        "prepare_pose_pwms": list(demo_cfg.prepare_pose_pwms),
        "target_class_aliases": list(demo_cfg.target_class_aliases),
        "observable_pregrasp_standoff_m": demo_cfg.observable_pregrasp_standoff_m,
        "near_approach_step_m": demo_cfg.near_approach_step_m,
        "grasp_height_offset_m": config["grasp_compensation"]["grasp_height_offset_m"],
        "full_lift_enabled": demo_cfg.full_lift_enabled,
        "max_stage": args.max_stage,
        "allow_missing_gripper_prad": bool(args.allow_missing_gripper_prad),
        "dry_run": bool(args.dry_run),
        "automatic_PDST": False,
    }, ensure_ascii=False))
    if args.check_config:
        print("CONFIG_OK hardware_opened=false")
        return 0

    if not args.dry_run:
        raise ValueError(
            "legacy bottle demo real motion is retired: its near-depth fallback "
            "can reuse a far target lock. Use tools/d435_yolo_grasp.py or "
            "tools/run_bottle_stage.sh; both require fresh RGB-D and all-six PRAD."
        )

    if not args.enable_arm:
        raise ValueError(
            "the demo contains motion; pass --enable_arm (use --dry_run true for simulated serial)"
        )

    from arm_grasp_pipeline.rknn_yolo_detector import RknnYolo11Detector

    serial_cfg = config["serial"]
    grasp_cfg = config["grasp"]
    adapter = SerialServoArmAdapter(
        port=args.serial_port or serial_cfg["port"],
        baudrate=args.baudrate or int(serial_cfg["baudrate"]),
        dry_run=bool(args.dry_run),
        initial_pwms=serial_cfg["initial_dry_run_pwms"],
        readback_retries=serial_cfg["readback_retries"],
        readback_timeout_s=serial_cfg["readback_timeout_s"],
        readback_tolerance_pwm=serial_cfg["readback_tolerance_pwm"],
        motion_settle_s=serial_cfg["motion_settle_s"],
    )
    arm = ArmMotion(
        adapter,
        kinematics,
        wrist_fixed_pwm=grasp_cfg["wrist_fixed_pwm"],
        servo_pwm_limits=grasp_cfg["servo_pwm_limits"],
    )
    confidence = float(config["runtime"]["confidence"] if args.conf is None else args.conf)
    detector = RknnYolo11Detector(
        args.model_path,
        args.yolo_dir,
        target=args.target,
        device_id=args.device_id,
        object_threshold=confidence,
    )
    rs_cfg = config["realsense"]
    camera = D435Source(
        rs_cfg["width"],
        rs_cfg["height"],
        rs_cfg["fps"],
        serial_number=rs_cfg.get("serial_number") or None,
    )
    if args.save_dir:
        save_dir = Path(args.save_dir).expanduser()
    else:
        save_dir = Path.home() / "rk3588_ai/debug_logs/bottle_grasp_demo" / datetime.now().strftime("%Y%m%d-%H%M%S")
    save_dir.mkdir(parents=True, exist_ok=True)
    logger = JsonlGraspLogger(str(save_dir / "events.jsonl"))
    vision = BottleDemoVision(camera, detector, config, demo_cfg, confidence)
    controller = BottleGraspDemo(
        arm,
        frames,
        config,
        vision,
        logger,
        approach_only=args.max_stage == "approach",
        allow_missing_gripper_prad=bool(args.allow_missing_gripper_prad),
        max_stage=args.max_stage,
        checkpoint_path=args.checkpoint_path,
    )
    resume_lock = None
    if args.resume_lock:
        lock_path = Path(args.resume_lock).expanduser()
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
        age_s = datetime.now().timestamp() - float(payload["wall_time"])
        if age_s < 0.0 or age_s > float(args.resume_lock_max_age_s):
            raise ValueError("resume target lock is stale: {:.1f}s".format(age_s))
        resume_lock = FarTargetLock(
            grasp_point_base=tuple(float(v) for v in payload["grasp_point_base"]),
            approach_direction_base=tuple(
                float(v) for v in payload["approach_direction_base"]
            ),
            depth_m=float(payload["depth_m"]),
            bbox=BBox(**payload["bbox"]),
            acquired_monotonic=float(payload["acquired_monotonic"]),
        )
    outcome = None
    try:
        detector.start()
        camera.start()
        if not args.dry_run:
            adapter.connect()
        outcome = controller.run(resume_lock=resume_lock)
        print("BOTTLE_DEMO_SUMMARY " + json.dumps(asdict(outcome), ensure_ascii=False))
        (save_dir / "summary.json").write_text(
            json.dumps(asdict(outcome), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return 0 if outcome.ok else 2
    finally:
        logger.close()
        # Closing the host serial object does not transmit PDST.  The heavy arm
        # deliberately holds the last PRAD-confirmed pose.
        print("ARM_HOLD_LAST_POSE automatic_PDST=false")
        adapter.close()
        try:
            camera.stop()
        except Exception:
            pass
        detector.close()


if __name__ == "__main__":
    raise SystemExit(main())
