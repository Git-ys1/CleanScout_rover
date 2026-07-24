#!/usr/bin/env python3
"""D435 + RKNN YOLO11 dynamic closed-loop grasp runtime (no ROS)."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import math
from pathlib import Path
import sys
import time

import numpy as np

try:
    import cv2
except ImportError:  # --help and all configuration gates remain PC-testable.
    cv2 = None

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.arm_motion import ArmMotion
from arm_grasp_pipeline.fixed_view import REQUIRED_WRIST_PWM, FixedViewCalibration
from arm_grasp_pipeline.geometry import FrameTransforms
from arm_grasp_pipeline.grasp_state_machine import (
    DynamicGraspStateMachine,
    DynamicObservation,
    JsonlGraspLogger,
)
from arm_grasp_pipeline.legacy_fixed_view_runtime import run_legacy_fixed_view
from arm_grasp_pipeline.official_kinematics import OfficialArmKinematics
from arm_grasp_pipeline.realsense_source import D435Source
from arm_grasp_pipeline.serial_servo_adapter import SerialServoArmAdapter
from arm_grasp_pipeline.target_depth import observe_depth_from_frame
from arm_grasp_pipeline.target_tracker import TargetTracker
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


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument(
        "--mode",
        choices=("observe", "center", "pregrasp", "approach", "grasp", "legacy_fixed_view"),
        default="observe",
    )
    parser.add_argument("--closed_loop", type=str2bool, default=True)
    parser.add_argument(
        "--max_stage", choices=("pregrasp", "approach", "close", "lift"), default=""
    )
    parser.add_argument("--max_approach_iterations", type=int, default=0)
    parser.add_argument("--target_class", default="")
    parser.add_argument("--dry_run", type=str2bool, default=True)
    parser.add_argument("--enable_arm", action="store_true")
    parser.add_argument("--save_dir", default="")
    parser.add_argument("--metrics_path", default="")
    parser.add_argument("--print_transforms", type=str2bool, default=True)
    parser.add_argument("--print_compensation", type=str2bool, default=True)
    parser.add_argument("--model_path", default="~/rk3588_ai/models/official_yolo11.rknn")
    parser.add_argument("--yolo_dir", default=str(DEFAULT_YOLO_DIR))
    parser.add_argument("--target", default="rk3588")
    parser.add_argument("--device_id", default=None)
    parser.add_argument("--conf", type=float, default=None)
    parser.add_argument("--serial_port", default="")
    parser.add_argument("--baudrate", type=int, default=0)
    parser.add_argument("--max_frames", type=int, default=0)
    parser.add_argument("--center_duration_s", type=float, default=3.0)
    parser.add_argument("--prepare_center_pose", type=str2bool, default=True)
    parser.add_argument("--no_show", action="store_true")
    return parser.parse_args(argv)


def load_config(path):
    with Path(path).expanduser().open("r", encoding="utf-8") as handle:
        return json.load(handle)


# Compatibility helpers used by the explicit legacy rollback tests/tools.
def reference_pose_mismatches(reference_pwms, actual_by_id, tolerance_pwm, servo_ids=None):
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


def same_target_observation(
    reference_center,
    reference_depth_m,
    target,
    target_depth_m,
    center_tolerance_px,
    depth_tolerance_m,
):
    if target is None or target_depth_m is None:
        return False
    dx = float(target.center[0]) - float(reference_center[0])
    dy = float(target.center[1]) - float(reference_center[1])
    return bool(
        math.hypot(dx, dy) <= float(center_tolerance_px)
        and abs(float(target_depth_m) - float(reference_depth_m))
        <= float(depth_tolerance_m)
    )


def validate_real_grasp_request(args, config, calibration=None):
    """Compatibility plus dynamic fail-before-connect safety gate."""

    executing = bool(
        getattr(args, "enable_arm", False)
        or getattr(args, "execute_on_lock", False)
    )
    if bool(getattr(args, "dry_run", True)) or not executing:
        return
    if not getattr(args, "enable_arm", False):
        raise ValueError("real output requires --enable_arm")
    serial_cfg = dict(config.get("serial", {}))
    grasp_cfg = dict(config.get("grasp", {}))
    kinematics_cfg = dict(config.get("kinematics", {}))
    joint_cfg = dict(config.get("joint_pwm_calibration", {}))
    if hasattr(args, "joint_pwm_calibrated") and not args.joint_pwm_calibrated:
        raise ValueError("real grasp requires explicit --joint_pwm_calibrated")
    if not bool(serial_cfg.get("joint_pwm_calibrated", False)):
        raise ValueError("config serial.joint_pwm_calibrated is false")
    if not bool(kinematics_cfg.get("calibrated", False)):
        raise ValueError("config kinematics.calibrated is false")
    if not bool(joint_cfg.get("calibrated", False)):
        raise ValueError("config joint_pwm_calibration.calibrated is false")
    if int(grasp_cfg.get("wrist_fixed_pwm", -1)) != REQUIRED_WRIST_PWM:
        raise ValueError("grasp Servo004 PWM must be {}".format(REQUIRED_WRIST_PWM))
    OfficialArmKinematics.from_config(kinematics_cfg, joint_cfg)
    if calibration is not None:
        calibration.require_real_grasp_ready(required_wrist_pwm=REQUIRED_WRIST_PWM)
        camera_mount = dict(config.get("camera_mount", {}))
        if not bool(camera_mount.get("frozen", False)):
            raise ValueError("camera mount relation is not frozen")
        if int(camera_mount.get("fixed_servo004_pwm", -1)) != REQUIRED_WRIST_PWM:
            raise ValueError("camera mount Servo004 PWM must be 1500")
        if list(grasp_cfg.get("retry_pose_pwms", [])) != list(
            calibration.reference_servo_pwms
        ):
            raise ValueError("grasp reference pose must equal fixed-view calibration pose")


def draw_depth(depth_m):
    if cv2 is None:
        return None
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


class LiveObservationSource:
    """D435/RKNN/TargetTracker adapter for the pure state machine boundary."""

    def __init__(self, source, detector, tracker, config, confidence, save_dir=None, show=False):
        self.source = source
        self.detector = detector
        self.tracker = tracker
        self.config = config
        self.confidence = float(confidence)
        self.depth_config = dict(config["depth_observation"])
        self.compensation = dict(config["grasp_compensation"])
        self.stale_timeout = float(config["closed_loop"]["stale_frame_timeout_s"])
        self.save_dir = None if save_dir is None else Path(save_dir)
        self.show = bool(show)
        self.frame_count = 0
        self.inference_count = 0
        self.previous_depth_m = None
        if self.save_dir is not None:
            self.save_dir.mkdir(parents=True, exist_ok=True)

    def _target_pixel(self, bbox):
        ratio = float(self.compensation.get("target_pixel_y_ratio", 0.5))
        return (
            float(bbox.center[0]),
            float(bbox.y1 + (bbox.y2 - bbox.y1) * ratio),
        )

    def _depth_sample_pixel(self, bbox):
        """Return the configured opaque-region depth probe inside the bbox.

        Transparent bottle bodies often return the background or several false
        stereo clusters.  The RGB grasp point remains independent (normally the
        bottle-body centre); only the depth ROI is centred on the opaque cap or
        label region selected by this ratio.
        """
        ratio = float(self.depth_config.get("sample_pixel_y_ratio", 0.5))
        if not 0.0 <= ratio <= 1.0:
            raise ValueError("depth_observation.sample_pixel_y_ratio must be in [0, 1]")
        return (
            float(bbox.center[0]),
            float(bbox.y1 + (bbox.y2 - bbox.y1) * ratio),
        )

    def _save_debug(self, frame, detections, tracking, depth):
        if cv2 is None:
            return
        color = frame.color_bgr.copy()
        for box in detections:
            cv2.rectangle(color, (box.x1, box.y1), (box.x2, box.y2), (255, 0, 0), 2)
        if tracking.bbox is not None:
            box = tracking.bbox
            cv2.rectangle(color, (box.x1, box.y1), (box.x2, box.y2), (0, 255, 0), 3)
        if self.show:
            cv2.imshow("D435 Dynamic Closed Loop", np.concatenate([color, draw_depth(frame.depth_m)], axis=1))
            cv2.waitKey(1)
        if self.save_dir is None or not tracking.motion_allowed:
            return
        stem = "frame_{:06d}".format(self.frame_count)
        cv2.imwrite(str(self.save_dir / (stem + "_rgb.jpg")), frame.color_bgr)
        cv2.imwrite(str(self.save_dir / (stem + "_depth.png")), draw_depth(frame.depth_m))
        cv2.imwrite(str(self.save_dir / (stem + "_overlay.jpg")), color)
        stats = np.zeros((300, 720, 3), dtype=np.uint8)
        fields = [] if depth is None else [
            "ok={} reason={}".format(depth.ok, depth.reason),
            "depth={} valid={}/ratio={:.3f}".format(depth.depth_m, depth.valid_count, depth.valid_ratio),
            "median={} MAD={} IQR={}".format(depth.median_m, depth.mad_m, depth.iqr_m),
            "ROI={}".format(depth.roi),
        ]
        for index, line in enumerate(fields):
            cv2.putText(stats, line, (15, 45 + 55 * index), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        cv2.imwrite(str(self.save_dir / (stem + "_depth_roi_stats.png")), stats)

    def next_observation(self, after_monotonic, expected_track_id):
        barrier = float(after_monotonic)
        for _ in range(121):
            frame = self.source.read_fresh_after(
                barrier,
                max_age_s=self.stale_timeout,
                require_aligned_rgbd=True,
            )
            self.frame_count += 1
            detections, _ = self.detector.infer(frame.color_bgr)
            self.inference_count += 1
            candidates = [box for box in detections if box.score >= self.confidence]
            candidate_depths = []
            for bbox in candidates:
                measured = observe_depth_from_frame(
                    frame,
                    bbox,
                    self.depth_config,
                    pixel_xy=self._depth_sample_pixel(bbox),
                )
                candidate_depths.append(measured.depth_m if measured.ok else None)
            tracking = self.tracker.update_result(
                candidates,
                frame.monotonic_timestamp,
                image_shape=frame.color_bgr.shape,
                depths_m=candidate_depths,
                now_monotonic_s=frame.arrival_monotonic_timestamp,
            )
            depth = None
            pixel = None
            if tracking.bbox is not None:
                pixel = self._target_pixel(tracking.bbox)
                depth_pixel = self._depth_sample_pixel(tracking.bbox)
                depth = observe_depth_from_frame(
                    frame,
                    tracking.bbox,
                    self.depth_config,
                    pixel_xy=depth_pixel,
                    previous_depth_m=self.previous_depth_m,
                    max_depth_jump_m=float(
                        self.depth_config.get(
                            "max_depth_jump_m",
                            self.config["target_tracker"]["max_depth_difference_m"],
                        )
                    ),
                )
                if depth.ok:
                    self.previous_depth_m = depth.depth_m
            self._save_debug(frame, candidates, tracking, depth)
            terminal_association_failure = bool(
                expected_track_id is not None
                and (tracking.lost or tracking.ambiguous or tracking.switched or not tracking.ok)
            )
            if tracking.motion_allowed or terminal_association_failure:
                return DynamicObservation(
                    acquired_monotonic=frame.monotonic_timestamp,
                    frame_timestamp=frame.device_timestamp_ms,
                    intrinsics=frame.intrinsics_for_detection,
                    image_shape_hw=frame.color_bgr.shape[:2],
                    track_id=tracking.track_id,
                    bbox=tracking.bbox,
                    pixel_grasp_point=pixel,
                    depth_observation=depth,
                    track_stable=tracking.stable,
                    track_switched=tracking.switched,
                    association_reason=tracking.association_reason,
                    color_bgr=frame.color_bgr,
                    depth_m=frame.depth_m,
                )
            barrier = frame.monotonic_timestamp
        raise RuntimeError("target did not become stable within 121 fresh frames")


def print_runtime_configuration(config, frames, print_transforms=True, print_compensation=True):
    print("DYNAMIC_FRAME_MODEL fixed_reference_used=false")
    print("ENVIRONMENT " + json.dumps(config["environment"], ensure_ascii=False))
    print("CALIBRATION_GATES " + json.dumps({
        "hand_eye": frames.hand_eye_calibrated,
        "open_tcp": frames.open_calibrated,
        "closed_tcp": frames.closed_calibrated,
        "joint_pwm": config["joint_pwm_calibration"]["calibrated"],
        "servo004_fixed_pwm": frames.servo004_fixed_pwm,
    }, ensure_ascii=False))
    if print_transforms:
        print("T_wrist_camera=" + json.dumps(frames.T_wrist_camera.tolist()))
        print("T_wrist_tcp_open=" + json.dumps(frames.T_wrist_tcp_open.tolist()))
        print("T_wrist_tcp_closed=" + json.dumps(frames.T_wrist_tcp_closed.tolist()))
    if print_compensation:
        print("GRASP_COMPENSATION=" + json.dumps(config["grasp_compensation"], ensure_ascii=False))


def resolve_stage(args):
    if args.mode == "pregrasp":
        required = "pregrasp"
    elif args.mode == "approach":
        required = "approach"
    elif args.mode == "grasp":
        required = args.max_stage or "lift"
    else:
        required = args.max_stage or "pregrasp"
    if args.max_stage and args.mode in ("pregrasp", "approach") and args.max_stage != required:
        raise ValueError("mode {} fixes max_stage={}".format(args.mode, required))
    return required


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.max_frames < 0 or args.max_approach_iterations < 0:
        raise ValueError("frame/iteration limits must be non-negative")
    config = load_config(args.config)
    if args.max_approach_iterations:
        config["closed_loop"]["max_approach_iterations"] = args.max_approach_iterations
    if args.target_class:
        config["target_tracker"]["target_class"] = args.target_class.strip().lower()
        config["runtime"]["target_class"] = args.target_class.strip().lower()
    if args.mode == "legacy_fixed_view":
        return run_legacy_fixed_view(args, config)
    if args.mode in ("approach", "grasp") and not args.closed_loop:
        raise ValueError("approach/grasp forbid --closed_loop false")
    motion_mode = args.mode in ("center", "pregrasp", "approach", "grasp")
    if motion_mode and not args.dry_run and not args.enable_arm:
        raise ValueError("real motion requires explicit --enable_arm")
    if args.mode == "observe" and args.enable_arm:
        raise ValueError("observe mode never enables arm motion")

    frames = FrameTransforms.from_config(config)
    kinematics = OfficialArmKinematics.from_config(
        config["kinematics"], config["joint_pwm_calibration"]
    )
    serial_cfg = config["serial"]
    grasp_cfg = config["grasp"]
    adapter = SerialServoArmAdapter(
        port=args.serial_port or serial_cfg["port"],
        baudrate=args.baudrate or int(serial_cfg["baudrate"]),
        dry_run=args.dry_run,
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
    metrics_path = args.metrics_path or (
        str(Path(args.save_dir).expanduser() / "grasp_events.jsonl") if args.save_dir else ""
    )
    logger = JsonlGraspLogger(metrics_path)
    machine = DynamicGraspStateMachine(
        arm,
        frames,
        config,
        logger=logger,
        allow_motion=motion_mode,
    )
    # This gate runs before detector, D435, and serial are opened.
    if motion_mode and not args.dry_run:
        machine.require_real_motion_calibration()
        if args.mode == "grasp" and resolve_stage(args) in ("close", "lift"):
            machine.require_real_close_calibration()
    print_runtime_configuration(
        config, frames, args.print_transforms, args.print_compensation
    )

    if cv2 is None:
        raise RuntimeError("opencv-python is required for D435 RKNN runtime")
    from arm_grasp_pipeline.rknn_yolo_detector import RknnYolo11Detector

    confidence = float(
        config["runtime"]["confidence"] if args.conf is None else args.conf
    )
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
    tracker = TargetTracker.from_config(
        config["target_tracker"],
        max_observation_age_s=config["closed_loop"]["stale_frame_timeout_s"],
    )
    live = LiveObservationSource(
        camera,
        detector,
        tracker,
        config,
        confidence,
        save_dir=args.save_dir or None,
        show=not args.no_show,
    )
    outcome = None
    try:
        detector.start()
        camera.start()
        if not args.dry_run:
            adapter.connect()  # observe uses PRAD read-only; no command is sent here.
        if args.mode == "observe":
            limit = args.max_frames or 1
            for _ in range(limit):
                # Observation cannot move the arm. It needs Servo000..004 for
                # the dynamic camera pose and reports Servo005 as unavailable
                # when the gripper PRAD is faulty. Every motion mode remains
                # strict Servo000..005 and fails before the next command.
                context = machine.observe_once(live, require_gripper_pwm=False)
                print("OBSERVE " + json.dumps({
                    "track_id": machine.track_id,
                    "actual_pwms_000_005": [
                        context.pwm_snapshot.pwms.get(servo_id)
                        for servo_id in range(6)
                    ],
                    "missing_pwm_ids": [
                        servo_id
                        for servo_id in range(6)
                        if servo_id not in context.pwm_snapshot.pwms
                    ],
                    "T_base_camera": context.T_base_camera.tolist(),
                    "target_base": list(context.compensation.final_grasp_point_base),
                    "depth": machine._depth_dict(context.observation.depth_observation),
                }, ensure_ascii=False))
            outcome = machine.outcome(True, "observe complete")
        elif args.mode == "center":
            center_cfg = dict(config["visual_centering"])
            if not bool(center_cfg.get("enabled", False)):
                raise ValueError("visual_centering.enabled=false")
            if args.center_duration_s <= 0.0 or args.center_duration_s > 15.0:
                raise ValueError("center_duration_s must be in (0, 15]")
            prepare = tuple(int(value) for value in center_cfg["prepare_pose_pwms"])
            if len(prepare) != 6 or prepare[4] != 1500:
                raise ValueError("visual centering prepare pose must contain six PWMs and Servo004=1500")
            if args.prepare_center_pose:
                prepared = arm.execute_assignments(
                    {servo_id: pwm for servo_id, pwm in enumerate(prepare)},
                    int(center_cfg["prepare_pose_duration_ms"]),
                )
                machine._execute_motion(prepared, "CENTER_PREPARE")
                barrier = float(prepared.motion_end_monotonic)
            else:
                barrier = float(arm.get_actual_pwm_snapshot().monotonic_timestamp)
            cfg_fields = {
                name: center_cfg[name]
                for name in CenteringConfig.__dataclass_fields__
                if name in center_cfg
            }
            centerer = PWMVisualCentering(CenteringConfig(**cfg_fields))
            deadline = time.monotonic() + float(args.center_duration_s)
            stable = 0
            iterations = 0
            while time.monotonic() < deadline:
                observation = live.next_observation(barrier, None)
                if observation.bbox is None or not observation.track_stable:
                    raise RuntimeError("visual centering lost stable bottle")
                snapshot = arm.get_actual_pwm_snapshot()
                updates = centerer.command(
                    observation.bbox,
                    observation.image_shape_hw,
                    snapshot.ordered(),
                )
                error_x = float(observation.bbox.center[0] - observation.image_shape_hw[1] / 2.0)
                error_y = float(observation.bbox.center[1] - observation.image_shape_hw[0] / 2.0)
                dead_zone_px = float(center_cfg["dead_zone_px"])
                aligned = (
                    abs(error_x) <= dead_zone_px
                    and abs(error_y) <= dead_zone_px
                )
                iterations += 1
                print("CENTER " + json.dumps({
                    "iteration": iterations,
                    "error_px": [error_x, error_y],
                    "aligned": aligned,
                    "actual_pwms_000_005": list(snapshot.ordered()),
                    "updates": updates,
                }, ensure_ascii=False))
                if aligned:
                    stable += 1
                    if stable >= int(center_cfg["stable_frames"]):
                        break
                    barrier = observation.acquired_monotonic
                    continue
                if not updates:
                    raise RuntimeError(
                        "visual centering saturated outside dead zone: "
                        f"error_px=({error_x:.1f},{error_y:.1f})"
                    )
                stable = 0
                updates[4] = 1500
                updates[5] = int(config["grasp"]["gripper_open_pwm"])
                result = arm.execute_assignments(
                    updates, int(center_cfg["duration_ms"])
                )
                machine._execute_motion(result, "VISUAL_CENTER")
                barrier = float(result.motion_end_monotonic)
                time.sleep(float(center_cfg["interval_s"]))
            outcome = machine.outcome(
                stable >= int(center_cfg["stable_frames"]),
                "visual centering converged" if stable >= int(center_cfg["stable_frames"])
                else "visual centering duration ended before convergence",
            )
        else:
            stage = resolve_stage(args)
            outcome = machine.run_to_stage(live, stage)
    finally:
        logger.close()
        # Never call stop()/PDST automatically: the heavy arm must hold.
        print("ARM_HOLD_LAST_POSE automatic_PDST=false")
        adapter.close()
        try:
            camera.stop()
        except Exception:
            pass
        detector.close()
        if cv2 is not None:
            cv2.destroyAllWindows()
    print("SUMMARY " + json.dumps(asdict(outcome), ensure_ascii=False, default=str))
    if args.save_dir and outcome is not None:
        summary_path = Path(args.save_dir).expanduser() / "grasp_summary.json"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(
            json.dumps(asdict(outcome), ensure_ascii=False, indent=2, default=str)
            + "\n",
            encoding="utf-8",
        )
    return 0 if outcome is not None and outcome.ok else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as exc:
        print("ERROR {}".format(exc), file=sys.stderr)
        raise SystemExit(2)
