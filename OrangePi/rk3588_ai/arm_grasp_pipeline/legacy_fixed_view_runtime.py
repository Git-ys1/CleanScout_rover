# coding: utf-8
"""Explicit, deprecated fixed-view rollback runtime.

This module is deliberately not imported or called by the production dynamic
state machine.  It exists only for an operator who explicitly selects
``legacy_fixed_view``.  The camera-to-base matrix is the historical
``T_base_camera_reference`` and therefore becomes invalid as soon as an
upstream arm joint moves; the resulting plan is intentionally open loop.

Even in this rollback path, writing a serial command is not considered motion
completion.  Real execution requires a complete Servo000..005 PRAD snapshot at
the calibrated reference pose before observation and after every plan stage.
No code in this module sends PDST.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import json
import math
from typing import Any, Mapping, Optional, Sequence, Tuple
import warnings

import numpy as np

from .arm_motion import ArmMotion
from .fixed_view import (
    REQUIRED_WRIST_PWM,
    FixedViewCalibration,
    ObjectGeometry,
    fixed_view_target_debug,
)
from .geometry import CameraIntrinsics
from .grasp_planner import (
    GraspConfig,
    GraspState,
    build_fixed_view_grasp_plan,
)
from .official_kinematics import OfficialArmKinematics
from .realsense_source import D435Source
from .serial_servo_adapter import SerialServoArmAdapter
from .target_depth import BBox, median_depth_in_bbox, stable_bbox


LEGACY_MODE = "legacy_fixed_view"


class LegacyFixedViewWarning(RuntimeWarning):
    """Visible warning emitted whenever the rollback runtime is entered."""


class LegacyFixedViewSafetyError(RuntimeError):
    """A fail-closed legacy runtime gate rejected observation or motion."""


@dataclass(frozen=True)
class LegacyObservation:
    """One stable, RGB-aligned fixed-view target measurement."""

    pixel_xy: Tuple[float, float]
    depth_m: float
    intrinsics: CameraIntrinsics

    def __post_init__(self) -> None:
        if len(self.pixel_xy) != 2 or not all(
            math.isfinite(float(value)) for value in self.pixel_xy
        ):
            raise ValueError("legacy observation pixel must contain two finite values")
        if not math.isfinite(float(self.depth_m)) or float(self.depth_m) <= 0.0:
            raise ValueError("legacy observation depth must be positive and finite")


def _arg(args: Any, name: str, default: Any = None) -> Any:
    if isinstance(args, Mapping):
        return args.get(name, default)
    return getattr(args, name, default)


def _dependency(dependencies: Any, name: str, default: Any = None) -> Any:
    if dependencies is None:
        return default
    if isinstance(dependencies, Mapping):
        return dependencies.get(name, default)
    return getattr(dependencies, name, default)


def _normalize_stage(value: Any) -> str:
    stage = str(value or "lift").strip().lower().replace("-", "_")
    aliases = {
        "open": "OPEN",
        "pregrasp": "PRE_GRASP",
        "pre_grasp": "PRE_GRASP",
        "approach": "APPROACH",
        "close": "CLOSE",
        "lift": "LIFT",
    }
    if stage not in aliases:
        raise ValueError("legacy max_stage must be open/pregrasp/approach/close/lift")
    return aliases[stage]


def _pose_mismatches(
    expected: Sequence[int],
    actual: Mapping[int, int],
    tolerance_pwm: int,
) -> Mapping[str, Mapping[str, Optional[int]]]:
    if len(expected) != 6:
        raise ValueError("legacy stage must contain six expected PWM values")
    tolerance = int(tolerance_pwm)
    if tolerance < 0:
        raise ValueError("readback tolerance must be non-negative")
    mismatches = {}
    for servo_id, target in enumerate(expected):
        measured = actual.get(servo_id)
        delta = None if measured is None else abs(int(measured) - int(target))
        if measured is None or delta > tolerance:
            mismatches[str(servo_id)] = {
                "target_pwm": int(target),
                "actual_pwm": None if measured is None else int(measured),
                "delta_pwm": delta,
            }
    return mismatches


def _real_motion_gate(
    args: Any,
    config: Mapping[str, Any],
    calibration: FixedViewCalibration,
) -> None:
    if bool(_arg(args, "dry_run", True)):
        return
    if not bool(_arg(args, "enable_arm", False)):
        raise LegacyFixedViewSafetyError(
            "real legacy fixed-view motion requires explicit --enable_arm"
        )
    if hasattr(args, "joint_pwm_calibrated") and not bool(
        _arg(args, "joint_pwm_calibrated", False)
    ):
        raise LegacyFixedViewSafetyError(
            "real legacy motion requires explicit --joint_pwm_calibrated"
        )
    try:
        calibration.require_real_grasp_ready(REQUIRED_WRIST_PWM)
    except ValueError as exc:
        raise LegacyFixedViewSafetyError(str(exc)) from exc

    serial_cfg = dict(config.get("serial", {}))
    kin_cfg = dict(config.get("kinematics", {}))
    pwm_cfg = dict(config.get("joint_pwm_calibration", {}))
    grasp_cfg = dict(config.get("grasp", {}))
    mount_cfg = dict(config.get("camera_mount", {}))
    runtime_cfg = dict(config.get("runtime", {}))
    if not bool(serial_cfg.get("joint_pwm_calibrated", False)):
        raise LegacyFixedViewSafetyError("serial joint PWM calibration is not frozen")
    if not bool(kin_cfg.get("calibrated", False)):
        raise LegacyFixedViewSafetyError("kinematics calibration is not frozen")
    if not bool(pwm_cfg.get("calibrated", False)):
        raise LegacyFixedViewSafetyError("joint PWM calibration is not frozen")
    if not bool(mount_cfg.get("frozen", False)):
        raise LegacyFixedViewSafetyError("fixed-view camera mount is not frozen")
    if not bool(mount_cfg.get("requires_fixed_servo004", False)):
        raise LegacyFixedViewSafetyError("legacy camera model must freeze Servo004")
    if int(mount_cfg.get("fixed_servo004_pwm", -1)) != REQUIRED_WRIST_PWM:
        raise LegacyFixedViewSafetyError("camera mount requires Servo004=1500")
    if int(grasp_cfg.get("wrist_fixed_pwm", -1)) != REQUIRED_WRIST_PWM:
        raise LegacyFixedViewSafetyError("grasp requires Servo004=1500")
    if tuple(int(value) for value in grasp_cfg.get("retry_pose_pwms", ())) != tuple(
        calibration.reference_servo_pwms
    ):
        raise LegacyFixedViewSafetyError(
            "grasp retry pose differs from the fixed-view calibration pose"
        )
    if bool(runtime_cfg.get("automatic_pdst", False)):
        raise LegacyFixedViewSafetyError("automatic PDST must remain disabled")


def _coerce_observation(value: Any) -> LegacyObservation:
    if isinstance(value, LegacyObservation):
        return value
    if isinstance(value, Mapping):
        return LegacyObservation(
            pixel_xy=tuple(value["pixel_xy"]),
            depth_m=float(value["depth_m"]),
            intrinsics=value["intrinsics"],
        )
    raise TypeError("observation_provider must return LegacyObservation or a mapping")


def _live_observation(args: Any, config: Mapping[str, Any], detector: Any, source: Any):
    runtime_cfg = dict(config.get("runtime", {}))
    grasp_cfg = GraspConfig.from_mapping(dict(config["grasp"]))
    target_class = str(
        _arg(args, "target_class", "") or runtime_cfg.get("target_class", "bottle")
    )
    confidence_arg = _arg(args, "conf", None)
    confidence = float(
        runtime_cfg.get("confidence", 0.25)
        if confidence_arg is None
        else confidence_arg
    )
    strategy = str(
        _arg(args, "strategy", "")
        or runtime_cfg.get("selection_strategy", "nearest_center")
    )
    # The dynamic tracker name is not meaningful to the old selector.
    if strategy not in ("nearest_center", "highest_conf"):
        strategy = "nearest_center"
    history = deque(maxlen=max(10, int(grasp_cfg.stable_frames) + 2))
    depth_history = deque(maxlen=max(3, int(grasp_cfg.depth_stable_frames)))
    max_frames = int(_arg(args, "max_frames", 0))
    if max_frames < 0:
        raise ValueError("max_frames must be non-negative")
    frame_count = 0
    while max_frames == 0 or frame_count < max_frames:
        frame = source.read()
        frame_count += 1
        if hasattr(frame, "require_aligned_rgbd"):
            frame.require_aligned_rgbd()
        detections, _ = detector.infer(frame.color_bgr)
        selected = detector.select_target(
            detections,
            frame.color_bgr.shape,
            target_class,
            confidence,
            strategy,
        )
        if selected is None:
            history.clear()
            depth_history.clear()
            continue
        history.append(selected)
        current_box = stable_bbox(
            list(history),
            max_center_jitter_px=grasp_cfg.max_center_jitter_px,
            min_frames=grasp_cfg.stable_frames,
        )
        if current_box is None:
            continue
        depth = median_depth_in_bbox(
            frame.depth_m,
            current_box,
            inner_ratio=grasp_cfg.depth_roi_inner_ratio,
        )
        if depth is None:
            depth_history.clear()
            continue
        depth_history.append(float(depth))
        if len(depth_history) < int(grasp_cfg.depth_stable_frames):
            continue
        if max(depth_history) - min(depth_history) > float(
            grasp_cfg.max_depth_jitter_m
        ):
            continue
        return LegacyObservation(
            pixel_xy=tuple(current_box.center),
            depth_m=float(np.median(np.asarray(depth_history, dtype=float))),
            intrinsics=frame.intrinsics_for_detection,
        )
    raise LegacyFixedViewSafetyError(
        "legacy target/depth did not stabilize within {} frames".format(max_frames)
    )


def _plan_rows(plan, arm: ArmMotion):
    rows = []
    for step in plan:
        row = step.as_dict()
        if step.state in (GraspState.OPEN, GraspState.CLOSE):
            row["command"] = arm.adapter.pack_partial_pwm_command(
                {5: int(step.gripper_pwm)}, int(step.duration_ms)
            )
        else:
            row["command"] = arm.pack_ik_command(step.ik, int(step.duration_ms))
        rows.append(row)
    return rows


def _execute_plan_with_prad(
    plan,
    arm: ArmMotion,
    tolerance_pwm: int,
) -> None:
    for step in plan:
        if step.state in (GraspState.OPEN, GraspState.CLOSE):
            result = arm.execute_assignments(
                {5: int(step.gripper_pwm)}, int(step.duration_ms)
            )
        else:
            result = arm.execute_ik(step.ik, int(step.duration_ms))
        if not result.ok:
            raise LegacyFixedViewSafetyError(
                "legacy {} command/readback failed: {}".format(
                    step.state.name, result.reason
                )
            )
        snapshot = result.readback_snapshot
        if snapshot is None:
            raise LegacyFixedViewSafetyError(
                "legacy {} has no PRAD completion evidence".format(step.state.name)
            )
        mismatches = _pose_mismatches(
            step.servo_pwms, snapshot.pwms, tolerance_pwm
        )
        if mismatches:
            raise LegacyFixedViewSafetyError(
                "legacy {} PRAD stage mismatch: {}".format(
                    step.state.name,
                    json.dumps(mismatches, ensure_ascii=False, sort_keys=True),
                )
            )
        print(
            "LEGACY_STAGE_PRAD "
            + json.dumps(
                {
                    "stage": step.state.name,
                    "simulated": bool(result.simulated),
                    "pwms": [int(snapshot.pwms[index]) for index in range(6)],
                },
                ensure_ascii=False,
            )
        )


def maybe_run_legacy_fixed_view(
    args: Any,
    config: Mapping[str, Any],
    dependencies: Any = None,
) -> Optional[int]:
    """Run only for an exact explicit selection; otherwise have no side effects."""

    if str(_arg(args, "mode", "")) != LEGACY_MODE:
        return None
    return run_legacy_fixed_view(args, config, dependencies)


def run_legacy_fixed_view(
    args: Any,
    config: Mapping[str, Any],
    dependencies: Any = None,
) -> int:
    """Observe, plan and optionally execute the explicit fixed-view rollback.

    ``dependencies`` is an optional mapping/object used by hardware-free tests.
    It may provide ``observation`` or ``observation_provider``, plus concrete
    ``kinematics``, ``adapter``, ``arm``, ``detector`` and ``source`` objects.
    Production callers normally omit it.
    """

    if str(_arg(args, "mode", "")) != LEGACY_MODE:
        raise LegacyFixedViewSafetyError(
            "legacy runtime requires explicit mode=legacy_fixed_view"
        )
    warnings.warn(
        "legacy_fixed_view is deprecated, fixed-reference and open-loop; "
        "use only as an explicit rollback",
        LegacyFixedViewWarning,
        stacklevel=2,
    )
    print(
        "LEGACY_FIXED_VIEW_DEPRECATED explicit_selection=true "
        "fixed_reference=true open_loop=true automatic_PDST=false"
    )

    calibration = FixedViewCalibration.from_mapping(
        dict(config.get("fixed_view_calibration", {}))
    )
    matrix = calibration.matrix()
    object_geometry = ObjectGeometry.from_mapping(
        dict(config.get("object_geometry", {}))
    )
    grasp_cfg = GraspConfig.from_mapping(dict(config.get("grasp", {})))
    if int(grasp_cfg.wrist_fixed_pwm) != REQUIRED_WRIST_PWM:
        raise LegacyFixedViewSafetyError("legacy rollback requires Servo004=1500")
    _real_motion_gate(args, config, calibration)

    kinematics = _dependency(dependencies, "kinematics")
    if kinematics is None:
        kinematics = OfficialArmKinematics.from_config(
            config["kinematics"], config["joint_pwm_calibration"]
        )
    adapter = _dependency(dependencies, "adapter")
    if adapter is None:
        serial_cfg = dict(config.get("serial", {}))
        adapter = SerialServoArmAdapter(
            port=str(_arg(args, "serial_port", "") or serial_cfg["port"]),
            baudrate=int(_arg(args, "baudrate", 0) or serial_cfg["baudrate"]),
            dry_run=bool(_arg(args, "dry_run", True)),
            initial_pwms=serial_cfg.get(
                "initial_dry_run_pwms", calibration.reference_servo_pwms
            ),
            readback_retries=int(serial_cfg.get("readback_retries", 3)),
            readback_timeout_s=float(serial_cfg.get("readback_timeout_s", 0.8)),
            readback_tolerance_pwm=int(
                serial_cfg.get("readback_tolerance_pwm", 40)
            ),
            motion_settle_s=float(serial_cfg.get("motion_settle_s", 0.15)),
        )
    requested_dry_run = bool(_arg(args, "dry_run", True))
    if bool(getattr(adapter, "dry_run", False)) != requested_dry_run:
        raise LegacyFixedViewSafetyError(
            "adapter dry_run state differs from the explicit runtime request"
        )
    arm = _dependency(dependencies, "arm")
    if arm is None:
        arm = ArmMotion(
            adapter,
            kinematics,
            wrist_fixed_pwm=grasp_cfg.wrist_fixed_pwm,
            servo_pwm_limits=grasp_cfg.servo_pwm_limits,
        )
    if getattr(arm, "adapter", None) is not adapter:
        raise LegacyFixedViewSafetyError(
            "legacy arm and runtime must use the same serial adapter"
        )

    detector = _dependency(dependencies, "detector")
    source = _dependency(dependencies, "source")
    detector_started = False
    source_started = False
    real_mode = not requested_dry_run
    try:
        if real_mode:
            adapter.connect()
            snapshot = arm.get_actual_pwm_snapshot()
            tolerance = int(
                config.get("serial", {}).get("reference_pose_tolerance_pwm", 40)
            )
            mismatches = _pose_mismatches(
                calibration.reference_servo_pwms, snapshot.pwms, tolerance
            )
            if mismatches:
                raise LegacyFixedViewSafetyError(
                    "arm is not at the calibrated fixed-view reference pose: "
                    + json.dumps(mismatches, ensure_ascii=False, sort_keys=True)
                )
            print(
                "LEGACY_REFERENCE_PRAD "
                + json.dumps(
                    {"pwms": list(snapshot.ordered(range(6))), "tolerance_pwm": tolerance},
                    ensure_ascii=False,
                )
            )

        observation_value = _dependency(dependencies, "observation")
        provider = _dependency(dependencies, "observation_provider")
        if observation_value is not None:
            observation = _coerce_observation(observation_value)
        elif provider is not None:
            observation = _coerce_observation(provider(args, config))
        else:
            if detector is None:
                from .rknn_yolo_detector import RknnYolo11Detector

                runtime_cfg = dict(config.get("runtime", {}))
                confidence_arg = _arg(args, "conf", None)
                confidence = float(
                    runtime_cfg.get("confidence", 0.25)
                    if confidence_arg is None
                    else confidence_arg
                )
                detector = RknnYolo11Detector(
                    str(_arg(args, "model_path", "~/rk3588_ai/models/official_yolo11.rknn")),
                    str(_arg(args, "yolo_dir", "~/rk3588_ai/rknn_model_zoo/examples/yolo11/python")),
                    target=str(_arg(args, "target", "rk3588")),
                    device_id=_arg(args, "device_id", None),
                    object_threshold=confidence,
                )
            if source is None:
                rs_cfg = dict(config.get("realsense", {}))
                source = D435Source(
                    int(rs_cfg.get("width", 640)),
                    int(rs_cfg.get("height", 480)),
                    int(rs_cfg.get("fps", 30)),
                    serial_number=rs_cfg.get("serial_number") or None,
                )
            detector.start()
            detector_started = True
            source.start()
            source_started = True
            observation = _live_observation(args, config, detector, source)

        debug = fixed_view_target_debug(
            observation.pixel_xy,
            observation.depth_m,
            observation.intrinsics,
            matrix,
            object_geometry,
        )
        max_stage = _normalize_stage(_arg(args, "max_stage", "lift"))
        plan = build_fixed_view_grasp_plan(
            debug.bottle_center_base_m,
            kinematics,
            grasp_cfg,
            max_stage=max_stage,
        )
        rows = _plan_rows(plan, arm)
        print(
            "LEGACY_FIXED_VIEW_LOCK "
            + json.dumps(
                {
                    "pixel_xy": list(debug.pixel_xy),
                    "depth_m": debug.depth_m,
                    "point_camera_m": list(debug.point_camera_m),
                    "bottle_center_base_m": list(debug.bottle_center_base_m),
                },
                ensure_ascii=False,
            )
        )
        print("LEGACY_FIXED_VIEW_PLAN " + json.dumps(rows, ensure_ascii=False))

        tolerance = int(config.get("serial", {}).get("readback_tolerance_pwm", 40))
        _execute_plan_with_prad(plan, arm, tolerance)
        print(
            "LEGACY_FIXED_VIEW_COMPLETE stage={} dry_run={} automatic_PDST=false".format(
                max_stage, not real_mode
            )
        )
        return 0
    finally:
        # Closing the transport never sends PDST.  The arm deliberately holds
        # its last verified pose for operator inspection.
        if real_mode:
            print("ARM_HOLD_LAST_POSE automatic_PDST=false")
        try:
            adapter.close()
        finally:
            if source_started:
                source.stop()
            if detector_started:
                detector.close()


__all__ = [
    "LEGACY_MODE",
    "LegacyFixedViewSafetyError",
    "LegacyFixedViewWarning",
    "LegacyObservation",
    "maybe_run_legacy_fixed_view",
    "run_legacy_fixed_view",
]
