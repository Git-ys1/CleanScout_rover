# coding: utf-8
"""Fail-closed one-button bottle demonstration controller.

This module is deliberately ROS-free and keeps the live hardware boundary
small.  Every physical move is a six-servo assignment accepted only after a
complete PRAD snapshot.  RGB-only near-field operation is permitted only
after a valid aligned-depth lock has established the target in the base frame.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import json
import math
from pathlib import Path
import time
from typing import Any, Iterable, Mapping, Optional, Sequence, Tuple

import numpy as np

from .geometry import (
    FrameTransforms,
    apply_grasp_compensation,
    apply_target_pixel_offset,
    depth_pixel_to_camera,
)
from .grasp_planner import (
    GraspConfig,
    approach_error_along_lateral_vertical,
    plan_final_insertion,
    plan_lift,
    plan_pregrasp,
)
from .target_depth import BBox, observe_depth_from_frame
from .visual_centering import CenteringConfig, PWMVisualCentering
from .serial_servo_adapter import PWMReadbackSnapshot


class BottleDemoStop(RuntimeError):
    """A fail-stop condition after which no further approach is allowed."""


@dataclass(frozen=True)
class BottleDemoConfig:
    target_class_aliases: Tuple[str, ...]
    prepare_pose_pwms: Tuple[int, int, int, int, int, int]
    prepare_duration_ms: int
    centering_timeout_s: float
    acquisition_pitch_step_pwm: int
    acquisition_pitch_max_pwm: int
    acquisition_move_duration_ms: int
    detection_stable_frames: int
    detection_max_frames: int
    observable_pregrasp_standoff_m: float
    observable_pregrasp_pitch_deg: float
    pregrasp_duration_ms: int
    grasp_height_offset_m: float
    minimum_reliable_depth_m: float
    near_depth_fallback_enabled: bool
    near_approach_step_m: float
    near_min_step_m: float
    near_close_distance_m: float
    near_final_tolerance_m: float
    near_max_forward_m: float
    near_step_duration_ms: int
    near_max_iterations: int
    approach_profile_standoff_pitch: Tuple[Tuple[float, float], ...]
    horizontal_only_from_standoff_m: float
    final_horizontal_insertion_m: float
    rgb_max_center_jump_px: float
    rgb_max_size_ratio: float
    rgb_reacquire_center_radius_px: float
    target_base_max_jump_m: float
    near_lateral_tolerance_m: float
    near_vertical_tolerance_m: float
    gripper_open_pwm: int
    gripper_close_pwm: int
    wrist_fixed_pwm: int
    gripper_close_duration_ms: int
    verify_lift_m: float
    verify_lift_duration_ms: int
    verify_rgb_max_center_shift_px: float
    verify_rgb_max_size_ratio: float
    full_lift_enabled: bool
    full_lift_additional_m: float
    full_lift_duration_ms: int

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> "BottleDemoConfig":
        values = dict(mapping)
        required = set(cls.__dataclass_fields__)
        missing = sorted(required.difference(values))
        if missing:
            raise ValueError("demo_grasp config missing: " + ", ".join(missing))
        values["target_class_aliases"] = tuple(
            normalize_class_name(value) for value in values["target_class_aliases"]
        )
        values["prepare_pose_pwms"] = tuple(
            int(value) for value in values["prepare_pose_pwms"]
        )
        values["approach_profile_standoff_pitch"] = tuple(
            (float(row["standoff_m"]), float(row["pitch_deg"]))
            for row in values["approach_profile_standoff_pitch"]
        )
        cfg = cls(**{name: values[name] for name in required})
        cfg.validate()
        return cfg

    def validate(self) -> None:
        if not self.target_class_aliases or any(not value for value in self.target_class_aliases):
            raise ValueError("target_class_aliases must contain a class name")
        if len(self.prepare_pose_pwms) != 6:
            raise ValueError("prepare_pose_pwms must contain Servo000..005")
        if self.prepare_pose_pwms[3] < 580 or self.prepare_pose_pwms[3] > 680:
            raise ValueError("demo prepare Servo003 must remain near the measured table-view PWM 620")
        if self.prepare_pose_pwms[4] != self.wrist_fixed_pwm or self.wrist_fixed_pwm != 1500:
            raise ValueError("Servo004 must remain fixed at PWM 1500")
        if self.prepare_pose_pwms[5] != self.gripper_open_pwm:
            raise ValueError("prepare pose must hold the configured open gripper PWM")
        if not 0.005 <= float(self.near_min_step_m) <= float(self.near_approach_step_m) <= 0.010:
            raise ValueError("near approach steps must remain within 5..10 mm")
        if not 0.0 <= float(self.near_close_distance_m) <= 0.02:
            raise ValueError("near_close_distance_m must be in 0..20 mm")
        if float(self.observable_pregrasp_standoff_m) <= float(self.minimum_reliable_depth_m) - 0.08:
            raise ValueError("observable pregrasp standoff is too short for the D435 near limit")
        if not math.isfinite(float(self.grasp_height_offset_m)):
            raise ValueError("grasp_height_offset_m must be finite")
        for name in (
            "centering_timeout_s",
            "minimum_reliable_depth_m",
            "near_max_forward_m",
            "verify_lift_m",
        ):
            if not math.isfinite(float(getattr(self, name))) or float(getattr(self, name)) <= 0.0:
                raise ValueError(name + " must be positive and finite")
        if int(self.detection_stable_frames) < 1 or int(self.detection_max_frames) < 1:
            raise ValueError("detection frame limits must be positive")
        if int(self.acquisition_pitch_step_pwm) <= 0:
            raise ValueError("acquisition_pitch_step_pwm must be positive")
        if not self.prepare_pose_pwms[3] < int(self.acquisition_pitch_max_pwm) <= 1100:
            raise ValueError("acquisition_pitch_max_pwm must be above prepare Servo003 and <=1100")
        if int(self.acquisition_move_duration_ms) < 20:
            raise ValueError("acquisition_move_duration_ms must be at least 20 ms")
        if int(self.near_max_iterations) < 1:
            raise ValueError("near_max_iterations must be positive")
        if len(self.approach_profile_standoff_pitch) > int(self.near_max_iterations):
            raise ValueError("approach profile exceeds near_max_iterations")
        previous = float(self.observable_pregrasp_standoff_m)
        for standoff, pitch in self.approach_profile_standoff_pitch:
            delta = previous - float(standoff)
            if not math.isclose(delta, float(self.near_approach_step_m), rel_tol=0.0, abs_tol=1e-9):
                raise ValueError("each approach profile waypoint must advance exactly near_approach_step_m")
            if standoff <= float(self.horizontal_only_from_standoff_m) and abs(float(pitch)) > 1e-9:
                raise ValueError("final approach profile must be horizontal")
            previous = float(standoff)
        if not math.isclose(
            previous,
            float(self.near_close_distance_m),
            rel_tol=0.0,
            abs_tol=float(self.near_final_tolerance_m),
        ):
            raise ValueError("approach profile must end at the close standoff")
        if not 0.005 <= float(self.final_horizontal_insertion_m) <= 0.010:
            raise ValueError("final_horizontal_insertion_m must remain within 5..10 mm")
        if not math.isclose(
            float(self.final_horizontal_insertion_m),
            float(self.near_close_distance_m),
            rel_tol=0.0,
            abs_tol=1e-9,
        ):
            raise ValueError("final insertion must carry the TCP from close standoff to object center")


@dataclass(frozen=True)
class VisionSample:
    frame: Any
    bbox: BBox
    depth: Any
    infer_ms: float


@dataclass(frozen=True)
class FarTargetLock:
    grasp_point_base: Tuple[float, float, float]
    approach_direction_base: Tuple[float, float, float]
    depth_m: float
    bbox: BBox
    acquired_monotonic: float


@dataclass(frozen=True)
class BottleDemoOutcome:
    ok: bool
    stage: str
    reason: str
    approach_steps: int
    cumulative_forward_m: float
    verification: str


def normalize_class_name(value: Any) -> str:
    return str(value).strip().lower().replace(" ", "")


def alias_candidates(
    detections: Iterable[BBox], aliases: Sequence[str], confidence: float
) -> Tuple[BBox, ...]:
    accepted = set(normalize_class_name(value) for value in aliases)
    return tuple(
        bbox for bbox in detections
        if float(bbox.score) >= float(confidence)
        and normalize_class_name(bbox.cls) in accepted
    )


def bbox_size_ratio(first: BBox, second: BBox) -> float:
    small = min(float(first.area), float(second.area))
    large = max(float(first.area), float(second.area))
    return math.inf if small <= 0.0 else large / small


def bbox_center_distance(first: BBox, second: BBox) -> float:
    return float(math.hypot(
        float(first.center[0] - second.center[0]),
        float(first.center[1] - second.center[1]),
    ))


class RGBIdentityGuard:
    """Associate one near-field alias without silently switching targets."""

    def __init__(
        self,
        aliases: Sequence[str],
        max_center_jump_px: float,
        max_size_ratio: float,
        initial_bbox: Optional[BBox] = None,
    ) -> None:
        self.aliases = tuple(normalize_class_name(value) for value in aliases)
        self.max_center_jump_px = float(max_center_jump_px)
        self.max_size_ratio = float(max_size_ratio)
        self.last_bbox = initial_bbox

    def associate(self, detections: Iterable[BBox], confidence: float) -> BBox:
        candidates = alias_candidates(detections, self.aliases, confidence)
        if not candidates:
            raise BottleDemoStop("RGB target lost (accepted aliases: {})".format(
                ",".join(self.aliases)
            ))
        if self.last_bbox is None:
            if len(candidates) != 1:
                raise BottleDemoStop("RGB target acquisition is ambiguous")
            selected = candidates[0]
        else:
            compatible = tuple(
                bbox for bbox in candidates
                if bbox_center_distance(self.last_bbox, bbox) <= self.max_center_jump_px
                and bbox_size_ratio(self.last_bbox, bbox) <= self.max_size_ratio
            )
            if len(compatible) != 1:
                raise BottleDemoStop(
                    "RGB target switched/lost: {} compatible detections".format(len(compatible))
                )
            selected = compatible[0]
        self.last_bbox = selected
        return selected


def select_initial_alias_target(
    detections: Iterable[BBox],
    aliases: Sequence[str],
    confidence: float,
    frame_shape: Sequence[int],
) -> Optional[BBox]:
    candidates = alias_candidates(detections, aliases, confidence)
    if not candidates:
        return None
    height, width = int(frame_shape[0]), int(frame_shape[1])
    return min(candidates, key=lambda bbox: (
        (bbox.center[0] - width / 2.0) ** 2
        + (bbox.center[1] - height / 2.0) ** 2
    ))


def full_hold_assignments(
    measured_pwms: Sequence[int], updates: Mapping[int, int], *, wrist_pwm: int = 1500
) -> Mapping[int, int]:
    values = [int(value) for value in measured_pwms]
    if len(values) != 6:
        raise ValueError("measured_pwms must contain Servo000..005")
    for servo_id, pwm in updates.items():
        index = int(servo_id)
        if index < 0 or index >= 6:
            raise ValueError("unknown Servo{:03d}".format(index))
        values[index] = int(pwm)
    values[4] = int(wrist_pwm)
    return {servo_id: pwm for servo_id, pwm in enumerate(values)}


def bounded_horizontal_step(
    remaining_to_close_m: float,
    configured_step_m: float,
    minimum_step_m: float,
    final_tolerance_m: float,
) -> float:
    remaining = float(remaining_to_close_m)
    if remaining <= float(final_tolerance_m):
        return 0.0
    step = min(float(configured_step_m), remaining)
    if step < float(minimum_step_m):
        raise BottleDemoStop(
            "remaining horizontal distance {:.4f} m is below safe step {:.4f} m"
            .format(remaining, float(minimum_step_m))
        )
    if not 0.005 <= step <= 0.010:
        raise BottleDemoStop("computed approach step is outside 5..10 mm")
    return step


class BottleDemoVision:
    def __init__(
        self,
        source: Any,
        detector: Any,
        config: Mapping[str, Any],
        demo: BottleDemoConfig,
        confidence: float,
    ) -> None:
        self.source = source
        self.detector = detector
        self.depth_cfg = dict(config["depth_observation"])
        self.demo = demo
        self.confidence = float(confidence)
        self.stale_timeout_s = float(config["closed_loop"]["stale_frame_timeout_s"])
        self.compensation = dict(config["grasp_compensation"])

    def _depth_sample_pixel(self, bbox: BBox) -> Tuple[float, float]:
        """Sample the configured visible bottle region, not the clear belly."""

        ratio = float(self.depth_cfg.get("sample_pixel_y_ratio", 0.5))
        if not 0.0 <= ratio <= 1.0:
            raise ValueError("depth_observation.sample_pixel_y_ratio must be in [0, 1]")
        return (
            float(bbox.center[0]),
            float(bbox.y1 + bbox.height * ratio),
        )
        if not math.isclose(
            float(self.compensation["grasp_height_offset_m"]),
            float(self.demo.grasp_height_offset_m),
            rel_tol=0.0,
            abs_tol=1e-9,
        ):
            raise ValueError(
                "demo_grasp.grasp_height_offset_m must equal grasp_compensation.grasp_height_offset_m"
            )

    def read_initial(self, after_monotonic: float) -> VisionSample:
        barrier = float(after_monotonic)
        guard: Optional[RGBIdentityGuard] = None
        hits = 0
        for _ in range(int(self.demo.detection_max_frames)):
            frame = self.source.read_fresh_after(
                barrier,
                max_age_s=self.stale_timeout_s,
                require_aligned_rgbd=True,
            )
            detections, infer_ms = self.detector.infer(frame.color_bgr)
            if guard is None:
                bbox = select_initial_alias_target(
                    detections,
                    self.demo.target_class_aliases,
                    self.confidence,
                    frame.color_bgr.shape,
                )
                if bbox is None:
                    hits = 0
                    barrier = frame.monotonic_timestamp
                    continue
                guard = RGBIdentityGuard(
                    self.demo.target_class_aliases,
                    self.demo.rgb_max_center_jump_px,
                    self.demo.rgb_max_size_ratio,
                    bbox,
                )
                hits = 1
            else:
                try:
                    bbox = guard.associate(detections, self.confidence)
                    hits += 1
                except BottleDemoStop:
                    guard = None
                    hits = 0
                    barrier = frame.monotonic_timestamp
                    continue
            depth = observe_depth_from_frame(
                frame,
                bbox,
                self.depth_cfg,
                pixel_xy=self._depth_sample_pixel(bbox),
            )
            if hits >= int(self.demo.detection_stable_frames):
                return VisionSample(frame, bbox, depth, float(infer_ms))
            barrier = frame.monotonic_timestamp
        raise BottleDemoStop("target did not become RGB-stable")

    def read_guarded(
        self, after_monotonic: float, guard: RGBIdentityGuard
    ) -> VisionSample:
        frame = self.source.read_fresh_after(
            float(after_monotonic),
            max_age_s=self.stale_timeout_s,
            require_aligned_rgbd=True,
        )
        detections, infer_ms = self.detector.infer(frame.color_bgr)
        bbox = guard.associate(detections, self.confidence)
        depth = observe_depth_from_frame(
            frame,
            bbox,
            self.depth_cfg,
            pixel_xy=self._depth_sample_pixel(bbox),
        )
        return VisionSample(frame, bbox, depth, float(infer_ms))


class BottleGraspDemo:
    """One-button, staged bottle grasp with an explicit near-depth fallback."""

    def __init__(
        self,
        arm: Any,
        frames: FrameTransforms,
        config: Mapping[str, Any],
        vision: BottleDemoVision,
        logger: Any,
        *,
        approach_only: bool = False,
        allow_missing_gripper_prad: bool = False,
        max_stage: str = "lift",
        checkpoint_path: Optional[str] = None,
    ) -> None:
        self.arm = arm
        self.frames = frames
        self.config = config
        self.demo = BottleDemoConfig.from_mapping(config["demo_grasp"])
        self.grasp = GraspConfig.from_mapping(config["grasp"])
        self.compensation = dict(config["grasp_compensation"])
        self.vision = vision
        self.logger = logger
        if approach_only and max_stage == "lift":
            max_stage = "approach"
        self.max_stage = str(max_stage)
        if self.max_stage not in ("center", "pregrasp", "approach", "lift"):
            raise ValueError("unknown bottle demo max_stage " + self.max_stage)
        self.approach_only = self.max_stage == "approach"
        self.allow_missing_gripper_prad = bool(allow_missing_gripper_prad)
        if self.allow_missing_gripper_prad and self.max_stage not in (
            "center", "pregrasp", "approach"
        ):
            raise ValueError(
                "missing Servo005 PRAD may only be waived for an open-gripper stage"
            )
        self.checkpoint_path = (
            None if not checkpoint_path else Path(checkpoint_path).expanduser()
        )
        self.stage = "INIT"
        self.last_motion_end = -math.inf
        self.approach_steps = 0
        self.cumulative_forward_m = 0.0
        self.verification = "not_attempted"

    def _log(self, event: str, **extra: Any) -> None:
        row = {
            "wall_time": time.time(),
            "monotonic_time": time.monotonic(),
            "demo_stage": self.stage,
            "event": event,
            "approach_steps": self.approach_steps,
            "cumulative_forward_m": self.cumulative_forward_m,
        }
        row.update(extra)
        self.logger.log(row)

    def _execute(self, assignments: Mapping[int, int], duration_ms: int, label: str, ik: Any = None):
        if set(int(key) for key in assignments) != set(range(6)):
            raise BottleDemoStop(label + " must command/hold all Servo000..005")
        result = self.arm.execute_assignments(assignments, int(duration_ms), ik=ik)
        if (
            not result.ok
            and self.allow_missing_gripper_prad
            and int(assignments[5]) == int(self.demo.gripper_open_pwm)
            and result.readback_snapshot is not None
            and set(range(5)).issubset(set(result.readback_snapshot.pwms))
        ):
            measured = result.readback_snapshot.pwms
            residuals = {
                servo_id: abs(int(measured[servo_id]) - int(assignments[servo_id]))
                for servo_id in range(5)
            }
            tolerance = int(self.config["serial"]["readback_tolerance_pwm"])
            if (
                max(residuals.values()) > tolerance
                and max(residuals.values()) <= 150
                and int(measured[4]) == int(self.demo.wrist_fixed_pwm)
            ):
                self._log(
                    "bounded_arrival_retry",
                    motion_label=label,
                    residual_pwm=residuals,
                    retry_count=1,
                )
                result = self.arm.execute_assignments(
                    assignments,
                    max(2000, min(int(duration_ms), 3000)),
                    ik=ik,
                )
        missing_gripper_only = False
        if not result.ok and self.allow_missing_gripper_prad:
            snapshot = result.readback_snapshot
            expected_pose_ids = set(range(5))
            missing_gripper_only = bool(
                int(assignments[5]) == int(self.demo.gripper_open_pwm)
                and result.command_packed
                and result.command_written
                and snapshot is not None
                and set(snapshot.pwms) == expected_pose_ids
            )
            if missing_gripper_only:
                tolerance = int(self.config["serial"]["readback_tolerance_pwm"])
                mismatches = {
                    servo_id: {
                        "expected_pwm": int(assignments[servo_id]),
                        "actual_pwm": int(snapshot.pwms[servo_id]),
                    }
                    for servo_id in range(5)
                    if abs(int(snapshot.pwms[servo_id]) - int(assignments[servo_id]))
                    > tolerance
                }
                if int(snapshot.pwms[4]) != int(self.demo.wrist_fixed_pwm):
                    mismatches[4] = {
                        "expected_pwm": int(self.demo.wrist_fixed_pwm),
                        "actual_pwm": int(snapshot.pwms[4]),
                    }
                if mismatches:
                    raise BottleDemoStop(
                        label + " Servo000..004 PRAD mismatch: " + str(mismatches)
                    )
        if not result.ok and not missing_gripper_only:
            raise BottleDemoStop(label + " failed: " + str(result.reason))
        if missing_gripper_only:
            self.last_motion_end = float(result.motion_end_monotonic)
            self._log(
                "motion_complete_missing_gripper_prad",
                motion_label=label,
                command=result.command,
                readback_pwms_000_004=list(result.readback_snapshot.ordered(range(5))),
                missing_readback_ids=[5],
                gripper_open_command_hold_pwm=int(self.demo.gripper_open_pwm),
            )
            return result
        if not result.readback_reached or result.readback_snapshot is None:
            raise BottleDemoStop(label + " has no complete PRAD arrival evidence")
        if set(result.readback_snapshot.pwms) != set(range(6)):
            raise BottleDemoStop(label + " PRAD snapshot is incomplete")
        self.last_motion_end = float(result.motion_end_monotonic)
        self._log(
            "motion_complete",
            motion_label=label,
            command=result.command,
            readback_pwms=list(result.readback_snapshot.ordered()),
        )
        return result

    def _snapshot(self) -> PWMReadbackSnapshot:
        """Return measured pose joints plus an explicit open-gripper hold token.

        Servo005 is synthesized only in the operator-requested approach-only
        emergency mode.  It is never described as measured and this mode can
        never enter CLOSE/VERIFY/LIFT.
        """

        if not self.allow_missing_gripper_prad:
            return self.arm.get_actual_pwm_snapshot()
        pose = self.arm.get_actual_wrist_pwm_snapshot()
        pwms = dict(pose.pwms)
        pwms[5] = int(self.demo.gripper_open_pwm)
        self._log(
            "observation_missing_gripper_prad",
            readback_pwms_000_004=list(pose.ordered(range(5))),
            missing_readback_ids=[5],
            gripper_open_command_hold_pwm=int(self.demo.gripper_open_pwm),
        )
        return PWMReadbackSnapshot(
            pwms,
            monotonic_timestamp=float(pose.monotonic_timestamp),
            attempts=int(pose.attempts),
            simulated=bool(pose.simulated),
        )

    def _snapshot_then_initial_sample(self) -> Tuple[Any, VisionSample]:
        snapshot = self._snapshot()
        barrier = max(float(snapshot.monotonic_timestamp), float(self.last_motion_end))
        return snapshot, self.vision.read_initial(barrier)

    def _target_lock(self, snapshot: Any, sample: VisionSample) -> FarTargetLock:
        if not sample.depth.ok or sample.depth.depth_m is None:
            raise BottleDemoStop("far aligned depth rejected: " + str(sample.depth.reason))
        depth_m = float(sample.depth.depth_m)
        if depth_m < float(self.demo.minimum_reliable_depth_m):
            raise BottleDemoStop("far depth is inside the D435 unreliable zone")
        raw_pixel = sample.bbox.center
        selected_pixel = apply_target_pixel_offset(
            raw_pixel, self.compensation["target_pixel_offset_px"]
        )
        point_camera = depth_pixel_to_camera(
            selected_pixel, depth_m, sample.frame.intrinsics_for_detection
        )
        T_base_wrist = self.arm.kin.forward_wrist_matrix_from_pwm(
            snapshot.ordered((0, 1, 2, 3))
        )
        T_base_camera = self.frames.base_camera(T_base_wrist)
        ordinary = dict(self.compensation)
        ordinary["final_insertion_m"] = 0.0
        compensated = apply_grasp_compensation(point_camera, T_base_camera, ordinary)
        lock = FarTargetLock(
            grasp_point_base=tuple(compensated.final_grasp_point_base),
            approach_direction_base=tuple(compensated.local_approach_frame[:3, 0]),
            depth_m=depth_m,
            bbox=sample.bbox,
            acquired_monotonic=float(sample.frame.monotonic_timestamp),
        )
        self._log(
            "valid_depth_lock",
            depth_m=depth_m,
            bbox=asdict(sample.bbox),
            actual_pwms=list(snapshot.ordered()),
            T_base_camera=T_base_camera,
            grasp_point_base=lock.grasp_point_base,
            approach_direction_base=lock.approach_direction_base,
        )
        if self.checkpoint_path is not None:
            payload = {
                "schema_version": 1,
                "wall_time": time.time(),
                "grasp_point_base": list(lock.grasp_point_base),
                "approach_direction_base": list(lock.approach_direction_base),
                "depth_m": float(lock.depth_m),
                "bbox": asdict(lock.bbox),
                "acquired_monotonic": float(lock.acquired_monotonic),
            }
            self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
            self.checkpoint_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            self._log("far_target_checkpoint_saved", path=str(self.checkpoint_path))
        return lock

    def _center(self) -> None:
        center_values = {
            name: self.config["visual_centering"][name]
            for name in CenteringConfig.__dataclass_fields__
            if name in self.config["visual_centering"]
        }
        centerer = PWMVisualCentering(CenteringConfig(**center_values))
        deadline = time.monotonic() + float(self.demo.centering_timeout_s)
        stable = 0
        while time.monotonic() < deadline:
            snapshot = self._snapshot()
            barrier = max(float(snapshot.monotonic_timestamp), float(self.last_motion_end))
            try:
                sample = self.vision.read_initial(barrier)
            except BottleDemoStop as exc:
                if str(exc) != "target did not become RGB-stable":
                    raise
                next_pitch = int(snapshot.ordered()[3]) + int(
                    self.demo.acquisition_pitch_step_pwm
                )
                if next_pitch > int(self.demo.acquisition_pitch_max_pwm):
                    raise BottleDemoStop(
                        "table-view acquisition scan reached Servo003 PWM {} without a stable bottle"
                        .format(self.demo.acquisition_pitch_max_pwm)
                    )
                full = full_hold_assignments(
                    snapshot.ordered(),
                    {3: next_pitch},
                    wrist_pwm=self.demo.wrist_fixed_pwm,
                )
                full[5] = int(self.demo.gripper_open_pwm)
                self._execute(
                    full,
                    int(self.demo.acquisition_move_duration_ms),
                    "TARGET_ACQUIRE_SCAN",
                )
                continue
            updates = centerer.command(
                sample.bbox, sample.frame.color_bgr.shape, snapshot.ordered()
            )
            height, width = sample.frame.color_bgr.shape[:2]
            error = (
                float(sample.bbox.center[0] - width / 2.0),
                float(sample.bbox.center[1] - height / 2.0),
            )
            dead_zone = float(self.config["visual_centering"]["dead_zone_px"])
            aligned = abs(error[0]) <= dead_zone and abs(error[1]) <= dead_zone
            self._log("centering_observation", error_px=error, aligned=aligned)
            if aligned:
                stable += 1
                if stable >= int(self.config["visual_centering"]["stable_frames"]):
                    return
                continue
            stable = 0
            if not updates:
                raise BottleDemoStop(
                    "visual centering saturated outside dead zone: error_px=({:.1f},{:.1f})"
                    .format(error[0], error[1])
                )
            full = full_hold_assignments(
                snapshot.ordered(),
                updates,
                wrist_pwm=self.demo.wrist_fixed_pwm,
            )
            full[5] = int(self.demo.gripper_open_pwm)
            self._execute(
                full,
                int(self.config["visual_centering"]["duration_ms"]),
                "VISUAL_CENTER",
            )
            time.sleep(float(self.config["visual_centering"]["interval_s"]))
        raise BottleDemoStop("visual centering timed out before convergence")

    def _move_pregrasp(self, lock: FarTargetLock) -> None:
        snapshot = self._snapshot()
        current = self.frames.base_tcp(
            self.arm.kin.forward_wrist_matrix_from_pwm(
                snapshot.ordered((0, 1, 2, 3))
            ),
            "closed",
        )
        observation_grasp = replace(
            self.grasp,
            pregrasp_pitch_deg=float(self.demo.observable_pregrasp_pitch_deg),
        )
        step = plan_pregrasp(
            current,
            lock.grasp_point_base,
            lock.approach_direction_base,
            self.frames.T_wrist_tcp_closed,
            self.arm.kin,
            observation_grasp,
            snapshot.ordered(),
            float(self.demo.observable_pregrasp_standoff_m),
            duration_ms=int(self.demo.pregrasp_duration_ms),
            tcp_name="closed",
        )
        assignments = full_hold_assignments(
            snapshot.ordered(),
            {servo_id: pwm for servo_id, pwm in enumerate(step.servo_pwms)},
            wrist_pwm=self.demo.wrist_fixed_pwm,
        )
        assignments[5] = int(self.demo.gripper_open_pwm)
        self._execute(assignments, step.duration_ms, "OBSERVABLE_PREGRASP", ik=step.ik)

    def _reacquire_after_pregrasp(self, previous: FarTargetLock) -> Tuple[FarTargetLock, RGBIdentityGuard, VisionSample]:
        snapshot, sample = self._snapshot_then_initial_sample()
        height, width = sample.frame.color_bgr.shape[:2]
        center_distance = math.hypot(
            sample.bbox.center[0] - width / 2.0,
            sample.bbox.center[1] - height / 2.0,
        )
        if center_distance > float(self.demo.rgb_reacquire_center_radius_px):
            raise BottleDemoStop("post-pregrasp RGB target is too far from the expected image center")
        lock = previous
        if sample.depth.ok and sample.depth.depth_m is not None:
            refreshed = self._target_lock(snapshot, sample)
            jump = float(np.linalg.norm(
                np.asarray(refreshed.grasp_point_base)
                - np.asarray(previous.grasp_point_base)
            ))
            if jump > float(self.demo.target_base_max_jump_m):
                raise BottleDemoStop(
                    "reobserved base target jumped {:.3f} m".format(jump)
                )
            lock = refreshed
        elif not self.demo.near_depth_fallback_enabled:
            raise BottleDemoStop("near depth invalid and RGB-only fallback is disabled")
        else:
            self._log(
                "near_depth_fallback_armed",
                reason=sample.depth.reason,
                retained_far_target_base=previous.grasp_point_base,
            )
        guard = RGBIdentityGuard(
            self.demo.target_class_aliases,
            self.demo.rgb_max_center_jump_px,
            self.demo.rgb_max_size_ratio,
            sample.bbox,
        )
        return lock, guard, sample

    def _approach(self, lock: FarTargetLock, guard: RGBIdentityGuard) -> VisionSample:
        latest: Optional[VisionSample] = None
        for target_standoff, target_pitch in self.demo.approach_profile_standoff_pitch:
            snapshot = self._snapshot()
            barrier = max(float(snapshot.monotonic_timestamp), float(self.last_motion_end))
            latest = self.vision.read_guarded(barrier, guard)
            if latest.depth.ok and latest.depth.depth_m is not None:
                refreshed = self._target_lock(snapshot, latest)
                jump = float(np.linalg.norm(
                    np.asarray(refreshed.grasp_point_base)
                    - np.asarray(lock.grasp_point_base)
                ))
                if jump > float(self.demo.target_base_max_jump_m):
                    raise BottleDemoStop("base target jump during approach {:.3f} m".format(jump))
                lock = refreshed
            elif not self.demo.near_depth_fallback_enabled:
                raise BottleDemoStop("aligned depth failed during approach")
            else:
                self._log("rgb_only_near_observation", depth_reason=latest.depth.reason)

            current = self.frames.base_tcp(
                self.arm.kin.forward_wrist_matrix_from_pwm(
                    snapshot.ordered((0, 1, 2, 3))
                ),
                "closed",
            )
            along, lateral, vertical = approach_error_along_lateral_vertical(
                current,
                lock.grasp_point_base,
                lock.approach_direction_base,
            )
            if abs(lateral) > float(self.demo.near_lateral_tolerance_m):
                raise BottleDemoStop("near RGB guard found excessive lateral error")
            if abs(vertical) > float(self.demo.near_vertical_tolerance_m):
                raise BottleDemoStop("near RGB guard found excessive vertical error")
            self._log(
                "near_alignment",
                error_along_lateral_vertical=(along, lateral, vertical),
                next_standoff_m=target_standoff,
                next_tool_pitch_deg=target_pitch,
                configured_step_m=self.demo.near_approach_step_m,
                actual_pwms=list(snapshot.ordered()),
            )
            if self.cumulative_forward_m + float(self.demo.near_approach_step_m) > float(self.demo.near_max_forward_m):
                raise BottleDemoStop("near-field cumulative forward limit reached")
            profile_grasp = replace(
                self.grasp,
                pregrasp_pitch_deg=float(target_pitch),
            )
            step = plan_pregrasp(
                current,
                lock.grasp_point_base,
                lock.approach_direction_base,
                self.frames.T_wrist_tcp_closed,
                self.arm.kin,
                profile_grasp,
                snapshot.ordered(),
                float(target_standoff),
                duration_ms=int(self.demo.near_step_duration_ms),
                tcp_name="closed",
            )
            step_norm = float(np.linalg.norm(np.asarray(step.step_xyz_m, dtype=float)))
            if not float(self.demo.near_min_step_m) <= step_norm <= 0.010 + 1e-9:
                raise BottleDemoStop(
                    "replanned Cartesian approach step {:.4f} m is outside 5..10 mm"
                    .format(step_norm)
                )
            if target_standoff <= float(self.demo.horizontal_only_from_standoff_m):
                if abs(float(step.pitch_deg)) > float(self.config["closed_loop"]["final_tool_pitch_tolerance_deg"]):
                    raise BottleDemoStop("final insertion profile is not horizontal")
                if abs(float(step.step_xyz_m[2])) > 0.001:
                    raise BottleDemoStop("final horizontal insertion changed base height")
            joint_deltas = tuple(
                abs(int(step.servo_pwms[index]) - int(snapshot.ordered()[index]))
                for index in range(4)
            )
            max_joint_step = int(self.config["closed_loop"]["max_joint_pwm_step"])
            if max(joint_deltas) > max_joint_step:
                raise BottleDemoStop(
                    "8 mm Cartesian step exceeds joint PWM limit {}: {}"
                    .format(max_joint_step, list(joint_deltas))
                )
            assignments = full_hold_assignments(
                snapshot.ordered(),
                {servo_id: pwm for servo_id, pwm in enumerate(step.servo_pwms)},
                wrist_pwm=self.demo.wrist_fixed_pwm,
            )
            assignments[5] = int(self.demo.gripper_open_pwm)
            label = (
                "FINAL_HORIZONTAL_8MM"
                if target_standoff <= float(self.demo.horizontal_only_from_standoff_m)
                else "RGB_GUARDED_APPROACH_8MM"
            )
            self._execute(assignments, step.duration_ms, label, ik=step.ik)
            self.approach_steps += 1
            self.cumulative_forward_m += float(self.demo.near_approach_step_m)
        if self.approach_only:
            snapshot = self._snapshot()
            latest = self.vision.read_guarded(
                max(float(snapshot.monotonic_timestamp), float(self.last_motion_end)),
                guard,
            )
            self._log(
                "approach_only_ready",
                configured_standoff_m=float(self.demo.near_close_distance_m),
                final_insertion_skipped_m=float(self.demo.final_horizontal_insertion_m),
                gripper_close_skipped=True,
                lift_skipped=True,
            )
            return latest
        # The profile stops 6 mm behind the grasp center.  Re-read RGB+PRAD,
        # then execute the final configured 6 mm horizontal insertion.  The
        # final insertion is still in the mandated 5..10 mm range.
        snapshot = self._snapshot()
        latest = self.vision.read_guarded(
            max(float(snapshot.monotonic_timestamp), float(self.last_motion_end)), guard
        )
        current = self.frames.base_tcp(
            self.arm.kin.forward_wrist_matrix_from_pwm(
                snapshot.ordered((0, 1, 2, 3))
            ),
            "closed",
        )
        along, lateral, vertical = approach_error_along_lateral_vertical(
            current,
            lock.grasp_point_base,
            lock.approach_direction_base,
        )
        if abs(along - float(self.demo.near_close_distance_m)) > float(self.demo.near_final_tolerance_m):
            raise BottleDemoStop("final 6 mm insertion gate has excessive along-axis error")
        if abs(lateral) > float(self.demo.near_lateral_tolerance_m):
            raise BottleDemoStop("final 6 mm insertion gate has excessive lateral error")
        if abs(vertical) > float(self.demo.near_vertical_tolerance_m):
            raise BottleDemoStop("final 6 mm insertion gate has excessive vertical error")
        final_step = plan_final_insertion(
            current,
            lock.approach_direction_base,
            float(self.demo.final_horizontal_insertion_m),
            float(self.demo.final_horizontal_insertion_m),
            self.frames.T_wrist_tcp_closed,
            self.arm.kin,
            self.grasp,
            snapshot.ordered(),
            duration_ms=int(self.demo.near_step_duration_ms),
            tcp_name="closed",
            horizontal_only=True,
            max_tool_pitch_deg=float(self.config["closed_loop"]["final_tool_pitch_tolerance_deg"]),
        )
        if final_step is None:
            raise BottleDemoStop("final horizontal insertion planner returned no step")
        final_deltas = tuple(
            abs(int(final_step.servo_pwms[index]) - int(snapshot.ordered()[index]))
            for index in range(4)
        )
        max_joint_step = int(self.config["closed_loop"]["max_joint_pwm_step"])
        if max(final_deltas) > max_joint_step:
            raise BottleDemoStop(
                "final 6 mm insertion exceeds joint PWM limit {}: {}"
                .format(max_joint_step, list(final_deltas))
            )
        assignments = full_hold_assignments(
            snapshot.ordered(),
            {servo_id: pwm for servo_id, pwm in enumerate(final_step.servo_pwms)},
            wrist_pwm=self.demo.wrist_fixed_pwm,
        )
        assignments[5] = int(self.demo.gripper_open_pwm)
        self._execute(
            assignments,
            final_step.duration_ms,
            "FINAL_HORIZONTAL_6MM_TO_GRASP_CENTER",
            ik=final_step.ik,
        )
        self.approach_steps += 1
        self.cumulative_forward_m += float(self.demo.final_horizontal_insertion_m)
        snapshot = self._snapshot()
        return self.vision.read_guarded(
            max(float(snapshot.monotonic_timestamp), float(self.last_motion_end)), guard
        )

    def _close_and_verify(self, guard: RGBIdentityGuard, before: VisionSample) -> None:
        snapshot = self._snapshot()
        close_assignments = full_hold_assignments(
            snapshot.ordered(),
            {5: self.demo.gripper_close_pwm},
            wrist_pwm=self.demo.wrist_fixed_pwm,
        )
        self._execute(close_assignments, self.demo.gripper_close_duration_ms, "CLOSE")
        # A close command is never treated as grasp success.  A fresh RGB
        # observation must still contain the guarded object before lifting.
        closed_snapshot = self.arm.get_actual_pwm_snapshot()
        before_lift = self.vision.read_guarded(
            max(float(closed_snapshot.monotonic_timestamp), self.last_motion_end), guard
        )
        current = self.frames.base_tcp(
            self.arm.kin.forward_wrist_matrix_from_pwm(
                closed_snapshot.ordered((0, 1, 2, 3))
            ),
            "closed",
        )
        lift = plan_lift(
            current,
            self.demo.verify_lift_m,
            self.frames.T_wrist_tcp_closed,
            self.arm.kin,
            self.grasp,
            closed_snapshot.ordered(),
            duration_ms=self.demo.verify_lift_duration_ms,
            tcp_name="closed",
            pitch_deg=None,
        )
        verify_lift_deltas = tuple(
            abs(int(lift.servo_pwms[index]) - int(closed_snapshot.ordered()[index]))
            for index in range(4)
        )
        max_joint_step = int(self.config["closed_loop"]["max_joint_pwm_step"])
        if max(verify_lift_deltas) > max_joint_step:
            raise BottleDemoStop(
                "15 mm verify lift exceeds joint PWM limit {}: {}"
                .format(max_joint_step, list(verify_lift_deltas))
            )
        lift_assignments = full_hold_assignments(
            closed_snapshot.ordered(),
            {servo_id: pwm for servo_id, pwm in enumerate(lift.servo_pwms)},
            wrist_pwm=self.demo.wrist_fixed_pwm,
        )
        lift_assignments[5] = int(self.demo.gripper_close_pwm)
        self._execute(lift_assignments, lift.duration_ms, "VERIFY_LIFT_15MM", ik=lift.ik)
        verify_snapshot = self.arm.get_actual_pwm_snapshot()
        after_lift = self.vision.read_guarded(
            max(float(verify_snapshot.monotonic_timestamp), self.last_motion_end), guard
        )
        shift = bbox_center_distance(before_lift.bbox, after_lift.bbox)
        ratio = bbox_size_ratio(before_lift.bbox, after_lift.bbox)
        if shift > float(self.demo.verify_rgb_max_center_shift_px) or ratio > float(self.demo.verify_rgb_max_size_ratio):
            self.verification = "uncertain_rgb_motion"
            raise BottleDemoStop(
                "15 mm lift did not retain the RGB target (shift {:.1f}px, size ratio {:.2f})"
                .format(shift, ratio)
            )
        self.verification = "rgb_attachment_candidate_after_15mm_lift"
        self._log("verify_lift_rgb_candidate", center_shift_px=shift, size_ratio=ratio)
        if not self.demo.full_lift_enabled:
            return
        snapshot = verify_snapshot
        current = self.frames.base_tcp(
            self.arm.kin.forward_wrist_matrix_from_pwm(
                snapshot.ordered((0, 1, 2, 3))
            ),
            "closed",
        )
        full = plan_lift(
            current,
            self.demo.full_lift_additional_m,
            self.frames.T_wrist_tcp_closed,
            self.arm.kin,
            self.grasp,
            snapshot.ordered(),
            duration_ms=self.demo.full_lift_duration_ms,
            tcp_name="closed",
            pitch_deg=None,
        )
        full_lift_deltas = tuple(
            abs(int(full.servo_pwms[index]) - int(snapshot.ordered()[index]))
            for index in range(4)
        )
        if max(full_lift_deltas) > max_joint_step:
            raise BottleDemoStop(
                "full lift exceeds joint PWM limit {}: {}"
                .format(max_joint_step, list(full_lift_deltas))
            )
        assignments = full_hold_assignments(
            snapshot.ordered(),
            {servo_id: pwm for servo_id, pwm in enumerate(full.servo_pwms)},
            wrist_pwm=self.demo.wrist_fixed_pwm,
        )
        assignments[5] = int(self.demo.gripper_close_pwm)
        self._execute(assignments, full.duration_ms, "FULL_LIFT", ik=full.ik)

    def run(self, resume_lock: Optional[FarTargetLock] = None) -> BottleDemoOutcome:
        try:
            if resume_lock is None:
                self.stage = "PREPARE"
                self._execute(
                    {servo_id: pwm for servo_id, pwm in enumerate(self.demo.prepare_pose_pwms)},
                    self.demo.prepare_duration_ms,
                    "PREPARE_TABLE_VIEW",
                )
                self.stage = "CENTER"
                self._center()
                if self.max_stage == "center":
                    return BottleDemoOutcome(
                        True,
                        "CENTER_READY",
                        "visual centering converged; no approach commanded",
                        0,
                        0.0,
                        "not_attempted_center_only",
                    )
                self.stage = "FAR_DEPTH_LOCK"
                snapshot, sample = self._snapshot_then_initial_sample()
                lock = self._target_lock(snapshot, sample)
                self.stage = "OBSERVABLE_PREGRASP"
                self._move_pregrasp(lock)
                self.stage = "REACQUIRE"
                lock, guard, sample = self._reacquire_after_pregrasp(lock)
                if self.max_stage == "pregrasp":
                    return BottleDemoOutcome(
                        True,
                        "PREGRASP_READY",
                        "observable pregrasp reached and freshly reacquired",
                        0,
                        0.0,
                        "not_attempted_pregrasp_only",
                    )
            else:
                if self.max_stage != "approach":
                    raise BottleDemoStop("resume lock is only accepted for approach stage")
                self.stage = "REACQUIRE"
                lock, guard, sample = self._reacquire_after_pregrasp(resume_lock)
            self.stage = "NEAR_HORIZONTAL_APPROACH"
            final_sample = self._approach(lock, guard)
            if self.approach_only:
                self.stage = "APPROACH_READY"
                return BottleDemoOutcome(
                    True,
                    self.stage,
                    "open gripper reached the 6 mm bottle-front gate; final insertion/close/lift intentionally disabled",
                    self.approach_steps,
                    self.cumulative_forward_m,
                    "not_attempted_approach_only",
                )
            self.stage = "CLOSE_VERIFY_LIFT"
            self._close_and_verify(guard, final_sample)
            self.stage = "DONE"
            return BottleDemoOutcome(
                True,
                self.stage,
                "RGB-guarded grasp candidate verified; inspect bottle-off-support physically",
                self.approach_steps,
                self.cumulative_forward_m,
                self.verification,
            )
        except Exception as exc:
            self.stage = "STOPPED"
            self._log("fail_stop", reason=str(exc))
            return BottleDemoOutcome(
                False,
                self.stage,
                str(exc),
                self.approach_steps,
                self.cumulative_forward_m,
                self.verification,
            )
