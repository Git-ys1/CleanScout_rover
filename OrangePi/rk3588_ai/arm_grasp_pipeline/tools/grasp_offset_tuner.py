#!/usr/bin/env python3
# coding: utf-8
"""Live RGB-D grasp-offset tuner that is physically incapable of arm motion.

Position the arm first with the separately gated ``pregrasp`` or ``approach``
command, then start this tool with the matching ``--stage`` label.  The tuner
opens the D435/RKNN and performs strict Servo000..005 PRAD reads, but constructs
the state machine with ``allow_motion=False`` and never calls a motion API.
Every keyboard edit is evaluated from a new aligned RGB-D frame and a new
six-axis PWM snapshot.  Saving creates an exact JSON backup and a readable
before/after report.

Space immediately latches PAUSE.  No image or PRAD update is consumed while
paused, and no mechanical-arm action is available at any time.  ESC exits
without saving.  Press ``p`` twice to save.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
import json
import math
from pathlib import Path
import sys
import time
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Tuple

import numpy as np

try:
    import cv2
except ImportError:  # --help and --check-only remain hardware independent.
    cv2 = None


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.arm_motion import ArmMotion  # noqa: E402
from arm_grasp_pipeline.geometry import FrameTransforms  # noqa: E402
from arm_grasp_pipeline.grasp_planner import (  # noqa: E402
    approach_error_along_lateral_vertical,
)
from arm_grasp_pipeline.grasp_state_machine import (  # noqa: E402
    DynamicGraspStateMachine,
    JsonlGraspLogger,
)
from arm_grasp_pipeline.official_kinematics import (  # noqa: E402
    OfficialArmKinematics,
)
from arm_grasp_pipeline.realsense_source import D435Source  # noqa: E402
from arm_grasp_pipeline.serial_servo_adapter import (  # noqa: E402
    SerialServoArmAdapter,
)
from arm_grasp_pipeline.target_tracker import TargetTracker  # noqa: E402
from arm_grasp_pipeline.tools.d435_yolo_grasp import (  # noqa: E402
    LiveObservationSource,
    draw_depth,
    str2bool,
)
from arm_grasp_pipeline.tools import tune_grasp_compensation as config_tuner  # noqa: E402


DEFAULT_CONFIG = ROOT / "config/arm_grasp_default.json"
DEFAULT_YOLO_DIR = Path.home() / "rk3588_ai/rknn_model_zoo/examples/yolo11/python"


KEY_BINDINGS: Mapping[int, Tuple[str, float]] = {
    ord("w"): ("along_mm", +1.0),
    ord("s"): ("along_mm", -1.0),
    ord("d"): ("lateral_mm", +1.0),
    ord("a"): ("lateral_mm", -1.0),
    ord("r"): ("vertical_mm", +1.0),
    ord("f"): ("vertical_mm", -1.0),
    ord("e"): ("depth_bias_mm", +1.0),
    ord("c"): ("depth_bias_mm", -1.0),
    ord("t"): ("surface_to_center_mm", +1.0),
    ord("g"): ("surface_to_center_mm", -1.0),
    ord("]"): ("pixel_y_ratio", +0.01),
    ord("["): ("pixel_y_ratio", -0.01),
}


def parse_args(argv: Optional[Iterable[str]] = None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument(
        "--stage",
        choices=("pregrasp", "final_align"),
        default="pregrasp",
        help="hard motion ceiling; final_align maps to dynamic approach with no close",
    )
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--dry_run", type=str2bool, default=True)
    parser.add_argument("--enable_arm", action="store_true")
    parser.add_argument("--serial_port", default="")
    parser.add_argument("--baudrate", type=int, default=0)
    parser.add_argument(
        "--model_path", default="~/rk3588_ai/models/official_yolo11.rknn"
    )
    parser.add_argument("--yolo_dir", default=str(DEFAULT_YOLO_DIR))
    parser.add_argument("--target", default="rk3588")
    parser.add_argument("--device_id", default=None)
    parser.add_argument("--target_class", default="")
    parser.add_argument("--conf", type=float, default=None)
    parser.add_argument("--step-mm", type=float, choices=(1.0, 2.0), default=1.0)
    parser.add_argument("--save_dir", default="")
    parser.add_argument("--metrics_path", default="")
    parser.add_argument("--report", default="")
    return parser.parse_args(argv)


def load_config(path: Path) -> MutableMapping[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("configuration root must be a JSON object")
    config_tuner.validate_config(value)
    return value


def apply_live_key(
    config: MutableMapping[str, object],
    key_code: int,
    step_mm: float,
) -> Optional[str]:
    """Apply one tuning key to an in-memory config, transactionally."""

    binding = KEY_BINDINGS.get(int(key_code))
    if binding is None:
        return None
    field, scale = binding
    step = float(step_mm)
    if step not in (1.0, 2.0):
        raise ValueError("step_mm must be 1 or 2")
    increment = scale if field == "pixel_y_ratio" else scale * step
    current = config_tuner.display_value(config, field)
    candidate = deepcopy(config)
    config_tuner.apply_assignment(
        candidate, "{}={}".format(field, current + increment)
    )
    config.clear()
    config.update(candidate)
    return field


def _active_tcp_text(config: Mapping[str, object]) -> str:
    tool = config.get("tool_tcp", {})
    if not isinstance(tool, Mapping):
        return "UNKNOWN"
    name = str(tool.get("active_grasp_tcp", "unknown")).lower()
    calibrated = bool(tool.get(name + "_calibrated", False))
    return "{} calibrated={}".format(name.upper(), calibrated)


def _overlay(context, config, *, paused: bool, step_mm: float, message: str):
    if cv2 is None:
        raise RuntimeError("opencv-python is required for the live tuner")
    observation = context.observation
    if observation.color_bgr is None or observation.depth_m is None:
        raise RuntimeError("live tuner requires RGB and aligned depth arrays")
    image = observation.color_bgr.copy()
    if observation.bbox is not None:
        box = observation.bbox
        cv2.rectangle(image, (box.x1, box.y1), (box.x2, box.y2), (0, 255, 0), 2)
    pixel = tuple(int(round(value)) for value in context.selected_pixel)
    cv2.drawMarker(
        image,
        pixel,
        (0, 0, 255),
        markerType=cv2.MARKER_CROSS,
        markerSize=18,
        thickness=2,
    )
    error = approach_error_along_lateral_vertical(
        context.T_base_tcp_actual,
        context.compensation.final_grasp_point_base,
        context.compensation.local_approach_frame[:3, 0],
    )
    compensation = config["grasp_compensation"]
    lines = [
        "PAUSED" if paused else "OBSERVE ONLY - NO MOTION",
        "TCP: {}".format(_active_tcp_text(config)),
        "track={} PWM={}".format(
            observation.track_id,
            list(
                context.pwm_snapshot.ordered(
                    tuple(sorted(context.pwm_snapshot.pwms))
                )
            ),
        ),
        "err along/lateral/vertical mm: {:+.1f} {:+.1f} {:+.1f}".format(
            *(float(value) * 1000.0 for value in error)
        ),
        "TCP xyz m: {}".format(
            np.round(context.T_base_tcp_actual[:3, 3], 4).tolist()
        ),
        "target xyz m: {}".format(
            np.round(context.compensation.final_grasp_point_base, 4).tolist()
        ),
        "bias a/l/v mm: {}".format(
            np.round(
                np.asarray(compensation["grasp_bias_approach_frame_m"]) * 1000.0,
                1,
            ).tolist()
        ),
        "depth/surface mm: {:+.1f} / {:.1f}".format(
            float(compensation["depth_bias_m"]) * 1000.0,
            float(compensation["object_surface_to_grasp_center_m"]) * 1000.0,
        ),
        "pixel_y_ratio={:.3f} step={:.0f}mm".format(
            float(compensation["target_pixel_y_ratio"]), float(step_mm)
        ),
        message,
    ]
    for index, line in enumerate(lines):
        color = (0, 0, 255) if index == 0 and paused else (255, 255, 255)
        cv2.putText(
            image,
            line,
            (10, 24 + index * 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.53,
            color,
            2,
            cv2.LINE_AA,
        )
    depth = draw_depth(observation.depth_m)
    return np.concatenate((image, depth), axis=1), error


def _help_text() -> str:
    return (
        "w/s along  a/d lateral  r/f vertical  e/c depth  "
        "t/g surface-to-center  [/ ] pixel-Y  1/2 step  "
        "u undo  0 reset  SPACE pause  p,p save  ESC quit"
    )


def _append_live_report(
    report_path: Path,
    *,
    stage: str,
    context,
    error: Tuple[float, float, float],
) -> None:
    with report_path.open("a", encoding="utf-8") as handle:
        handle.write("\n## Live observation at save\n\n")
        handle.write("- Stage ceiling: `{}`\n".format(stage))
        handle.write("- Fresh frame monotonic time: `{}`\n".format(
            context.observation.acquired_monotonic
        ))
        handle.write("- PRAD PWM snapshot: `{}`\n".format(
            dict(sorted(context.pwm_snapshot.pwms.items()))
        ))
        handle.write("- Error [along, lateral, vertical] m: `{}`\n".format(
            [float(value) for value in error]
        ))
        handle.write("- Active TCP: `closed`\n")
        handle.write("- Live D435/RKNN/PRAD access: `true`\n")
        handle.write("- Arm motion API enabled: `false`\n")
        handle.write("- No close or lift command was available in this tool.\n")


def _run_live(args, config_path: Path, initial):
    if args.enable_arm:
        raise ValueError(
            "grasp_offset_tuner is observation-only; position with a staged "
            "command first and omit --enable_arm"
        )
    if cv2 is None:
        raise RuntimeError("opencv-python is required for live tuning")

    config = deepcopy(initial)
    if args.target_class:
        name = args.target_class.strip().lower()
        config["target_tracker"]["target_class"] = name
        config["runtime"]["target_class"] = name
    frames = FrameTransforms.from_config(config)
    kin = OfficialArmKinematics.from_config(
        config["kinematics"], config["joint_pwm_calibration"]
    )
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
        kin,
        wrist_fixed_pwm=grasp_cfg["wrist_fixed_pwm"],
        servo_pwm_limits=grasp_cfg["servo_pwm_limits"],
    )
    save_dir = (
        Path(args.save_dir).expanduser()
        if args.save_dir
        else Path.home()
        / "rk3588_ai/debug_logs/grasp_offset_tuner"
        / datetime.now().strftime("%Y%m%d-%H%M%S")
    )
    save_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = (
        Path(args.metrics_path).expanduser()
        if args.metrics_path
        else save_dir / "events.jsonl"
    )
    logger = JsonlGraspLogger(str(metrics_path))
    observer = DynamicGraspStateMachine(
        arm, frames, config, logger=logger, allow_motion=False
    )
    if not args.dry_run:
        observer.require_real_motion_calibration()

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
    camera_cfg = config["realsense"]
    camera = D435Source(
        camera_cfg["width"],
        camera_cfg["height"],
        camera_cfg["fps"],
        serial_number=camera_cfg.get("serial_number") or None,
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
        save_dir=str(save_dir),
        show=False,
    )

    history: List[MutableMapping[str, object]] = []
    working = deepcopy(config)
    startup = deepcopy(config)
    step_mm = float(args.step_mm)
    paused = False
    save_armed_until = 0.0
    message = _help_text()
    last_context = None
    last_error = (math.nan, math.nan, math.nan)
    try:
        detector.start()
        camera.start()
        if not args.dry_run:
            adapter.connect()
        print(
            "TUNER_OBSERVE_ONLY stage_label={} motion_available=false "
            "close_available=false lift_available=false"
            .format(args.stage)
        )

        while True:
            if not paused:
                observer.comp_cfg = dict(working["grasp_compensation"])
                live.compensation = dict(working["grasp_compensation"])
                context = observer.observe_once(
                    live, require_gripper_pwm=True
                )
                display, error = _overlay(
                    context,
                    working,
                    paused=False,
                    step_mm=step_mm,
                    message=message,
                )
                last_context = context
                last_error = error
            else:
                if last_context is None:
                    raise RuntimeError("pause requested before the first observation")
                display, _ = _overlay(
                    last_context,
                    working,
                    paused=True,
                    step_mm=step_mm,
                    message=message,
                )
            cv2.imshow("Grasp Offset Tuner", display)
            key = cv2.waitKey(0 if paused else 30) & 0xFF
            if key == 255:
                continue
            if key == 27:
                print("TUNER_EXIT saved=false")
                return 0
            if key == ord(" "):
                paused = not paused
                message = "PAUSE latched" if paused else "RESUME; next frame must be fresh"
                print("TUNER_PAUSE {}".format(str(paused).lower()))
                continue
            if key == ord("1") or key == ord("2"):
                step_mm = float(chr(key))
                message = "step set to {:.0f} mm".format(step_mm)
                continue
            if key == ord("u"):
                if history:
                    working = history.pop()
                    message = "undo; fresh observation required"
                else:
                    message = "undo history empty"
                continue
            if key == ord("0"):
                history.append(deepcopy(working))
                working = deepcopy(startup)
                message = "reset to startup values; fresh observation required"
                continue
            if key == ord("p"):
                now = time.monotonic()
                if now > save_armed_until:
                    save_armed_until = now + 5.0
                    message = "press p again within 5 s to backup and save"
                    continue
                report = (
                    Path(args.report).expanduser()
                    if args.report
                    else save_dir / "grasp_offset_tuning.md"
                )
                backup, report_path = config_tuner.save_config(
                    config_path, initial, working, report_path=report
                )
                _append_live_report(
                    report_path,
                    stage=args.stage,
                    context=last_context,
                    error=last_error,
                )
                print("CONFIG_BACKUP {}".format(backup))
                print("CONFIG_WRITTEN {}".format(config_path))
                print("REPORT_WRITTEN {}".format(report_path))
                return 0
            if key == ord("m"):
                history.append(deepcopy(working))
                radius = config_tuner.display_value(working, "object_radius_mm")
                config_tuner.apply_assignment(
                    working, "surface_to_center_mm={}".format(radius)
                )
                message = "surface_to_center synchronized to bottle radius"
                continue
            candidate = deepcopy(working)
            changed = apply_live_key(candidate, key, step_mm)
            if changed is not None:
                history.append(deepcopy(working))
                working = candidate
                message = "{} changed; recomputing from fresh RGB-D/PWM".format(
                    changed
                )
                print(
                    "TUNER_UPDATE {}={:+.3f} fresh_observation_required=true"
                    .format(changed, config_tuner.display_value(working, changed))
                )
            else:
                message = _help_text()
    finally:
        logger.close()
        print("ARM_HOLD_LAST_POSE automatic_PDST=false")
        adapter.close()
        try:
            camera.stop()
        except Exception:
            pass
        detector.close()
        cv2.destroyAllWindows()


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    config_path = Path(args.config).expanduser().resolve()
    initial = load_config(config_path)
    if args.check_only:
        print(config_tuner.render_current(initial))
        print(
            "LIVE_TUNER_CHECK_OK stages=pregrasp,final_align "
            "motion_available=false close_available=false lift_available=false "
            "default_dry_run=true"
        )
        return 0
    return _run_live(args, config_path, initial)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as exc:
        print("ERROR {}".format(exc), file=sys.stderr)
        raise SystemExit(2)
