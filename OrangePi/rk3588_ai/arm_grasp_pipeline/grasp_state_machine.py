# coding: utf-8
"""Dynamic eye-on-arm closed-loop grasp state machine.

The production path in this module never reads a fixed base-to-camera matrix.
Each coordinate estimate is paired with a complete PRAD snapshot and uses
``FK(actual Servo000..003) @ T_wrist_camera``.  Each motion invalidates every
older RGB-D observation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
import json
import math
from pathlib import Path
import time
from typing import Any, Dict, Mapping, Optional, Tuple

import numpy as np

from .arm_motion import ArmMotion, MotionResult
from .geometry import (
    CameraIntrinsics,
    FrameTransforms,
    GraspCompensationResult,
    apply_grasp_compensation,
    apply_target_pixel_offset,
    depth_pixel_to_camera,
)
from .grasp_planner import (
    DynamicPlanStep,
    GraspConfig,
    GraspState,
    approach_error_along_lateral_vertical,
    plan_final_insertion,
    plan_lift,
    plan_next_approach_step,
    plan_pregrasp,
)
from .serial_servo_adapter import PWMReadbackSnapshot
from .target_depth import BBox
from .visual_centering import CenteringConfig, PWMVisualCentering


class ClosedLoopStop(RuntimeError):
    """A fail-stop condition; callers must not issue another approach command."""


class RecoverableObservationStop(ClosedLoopStop):
    """A target/depth failure eligible for the explicitly gated backoff path."""


@dataclass(frozen=True)
class DynamicObservation:
    """One aligned RGB-D detection already associated by TargetTracker."""

    acquired_monotonic: float
    frame_timestamp: float
    intrinsics: CameraIntrinsics
    image_shape_hw: Tuple[int, int]
    track_id: Optional[int]
    bbox: Optional[BBox]
    pixel_grasp_point: Optional[Tuple[float, float]]
    depth_observation: Optional[Any]
    track_stable: bool = False
    track_switched: bool = False
    association_reason: str = ""
    color_bgr: Optional[np.ndarray] = None
    depth_m: Optional[np.ndarray] = None

    def __post_init__(self):
        if not math.isfinite(float(self.acquired_monotonic)):
            raise ValueError("observation acquired_monotonic must be finite")
        if not math.isfinite(float(self.frame_timestamp)):
            raise ValueError("observation frame_timestamp must be finite")
        if len(self.image_shape_hw) != 2 or min(self.image_shape_hw) <= 0:
            raise ValueError("image_shape_hw must contain positive height and width")


@dataclass(frozen=True)
class ObservationContext:
    observation: DynamicObservation
    pwm_snapshot: PWMReadbackSnapshot
    T_base_wrist: np.ndarray
    T_base_camera: np.ndarray
    T_base_tcp_actual: np.ndarray
    selected_pixel: Tuple[float, float]
    raw_point_camera: np.ndarray
    compensation: GraspCompensationResult
    error_along_lateral_vertical: Optional[Tuple[float, float, float]] = None


@dataclass(frozen=True)
class ClosedLoopOutcome:
    ok: bool
    state: GraspState
    reason: str
    track_id: Optional[int]
    approach_iterations: int
    cumulative_approach_m: float
    commands_executed: int
    grasp_verification: str = "not_attempted"


@dataclass(frozen=True)
class GraspVerification:
    status: str
    reason: str
    relative_camera_shift_m: Optional[float]
    base_object_shift_m: Optional[float]
    base_object_vertical_shift_m: Optional[float]

    def as_dict(self):
        return asdict(self)


class JsonlGraspLogger:
    """Flush-on-write JSONL logger usable on Python 3.8 and in dry-run tests."""

    def __init__(self, path: Optional[str] = None):
        self.path = None if not path else Path(path).expanduser()
        self.records = []
        self._handle = None
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._handle = self.path.open("a", encoding="utf-8")

    @staticmethod
    def _jsonable(value):
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, np.generic):
            return value.item()
        if is_dataclass(value):
            return {
                key: JsonlGraspLogger._jsonable(item)
                for key, item in asdict(value).items()
                if key not in ("color_bgr", "depth_m")
            }
        if isinstance(value, Mapping):
            return {
                str(key): JsonlGraspLogger._jsonable(item)
                for key, item in value.items()
            }
        if isinstance(value, (tuple, list)):
            return [JsonlGraspLogger._jsonable(item) for item in value]
        if isinstance(value, GraspState):
            return value.name
        return value

    def log(self, record: Mapping[str, Any]):
        row = self._jsonable(dict(record))
        self.records.append(row)
        if self._handle is not None:
            self._handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            self._handle.flush()

    def close(self):
        if self._handle is not None:
            self._handle.close()
            self._handle = None


class DynamicGraspStateMachine:
    """Observe, reacquire and approach using fresh image/PWM pairs only."""

    def __init__(
        self,
        arm: ArmMotion,
        frames: FrameTransforms,
        config: Mapping,
        logger: Optional[JsonlGraspLogger] = None,
        allow_motion: bool = False,
    ) -> None:
        self.arm = arm
        self.frames = frames
        self.config = config
        self.logger = logger or JsonlGraspLogger()
        self.allow_motion = bool(allow_motion)
        self.grasp_cfg = GraspConfig.from_mapping(dict(config.get("grasp", {})))
        self.comp_cfg = dict(config.get("grasp_compensation", {}))
        self.loop_cfg = dict(config.get("closed_loop", {}))
        self.center_cfg = dict(config.get("visual_centering", {}))
        self.state = GraspState.INIT
        self.track_id: Optional[int] = None
        self.last_motion_end_monotonic = -math.inf
        self.last_frame_monotonic = -math.inf
        self.approach_iterations = 0
        self.cumulative_approach_m = 0.0
        self.commands_executed = 0
        self.stop_reason = ""
        self.grasp_verification = "not_attempted"
        self._validate_config()

    def _validate_config(self):
        required_loop = {
            "max_approach_iterations",
            "max_cumulative_approach_m",
            "max_approach_time_s",
            "max_joint_pwm_step",
            "final_align_stable_frames",
            "final_lateral_tolerance_m",
            "final_vertical_tolerance_m",
            "final_along_tolerance_m",
            "safe_roi_margin_px",
            "stale_frame_timeout_s",
            "minimum_reliable_aligned_depth_m",
            "near_depth_loss_policy",
            "final_motion_horizontal_only",
            "final_tool_pitch_tolerance_deg",
            "coarse_center_enabled",
            "coarse_center_max_iterations",
            "depth_lock_min_frames",
            "depth_lock_max_base_spread_m",
            "retry_backoff_enabled",
            "max_retries",
            "retry_backoff_m",
        }
        missing = sorted(required_loop.difference(self.loop_cfg))
        if missing:
            raise ValueError("closed_loop config missing: {}".format(", ".join(missing)))
        if not bool(self.config.get("joint_pwm_calibration", {}).get("calibrated", False)):
            raise ValueError("joint PWM calibration is not marked calibrated")
        if int(self.grasp_cfg.wrist_fixed_pwm) != self.frames.servo004_fixed_pwm:
            raise ValueError("Servo004 fixed PWM differs between frames and grasp config")
        minimum = float(self.comp_cfg.get("min_approach_step_m", float("nan")))
        maximum = float(self.comp_cfg.get("max_approach_step_m", float("nan")))
        configured = float(self.comp_cfg.get("approach_step_m", float("nan")))
        if not (0.005 <= minimum <= configured <= maximum <= 0.010):
            raise ValueError("approach step config must remain in 5..10 mm")
        if float(self.comp_cfg.get("pregrasp_standoff_m", 0.0)) <= 0.0:
            raise ValueError("pregrasp_standoff_m must be positive")
        depth_lock_frames = int(self.loop_cfg["depth_lock_min_frames"])
        depth_lock_spread = float(
            self.loop_cfg["depth_lock_max_base_spread_m"]
        )
        if depth_lock_frames < 2:
            raise ValueError("depth_lock_min_frames must be at least 2")
        if not 0.0 < depth_lock_spread <= 0.050:
            raise ValueError(
                "depth_lock_max_base_spread_m must be in (0, 0.050]"
            )
        retry_count = int(self.loop_cfg["max_retries"])
        retry_backoff_m = float(self.loop_cfg["retry_backoff_m"])
        if retry_count < 0 or retry_count > 3:
            raise ValueError("max_retries must be in 0..3")
        if not 0.005 <= retry_backoff_m <= 0.010:
            raise ValueError("retry_backoff_m must remain in 5..10 mm")
        if bool(self.loop_cfg["retry_backoff_enabled"]) and retry_count < 1:
            raise ValueError(
                "retry_backoff_enabled requires max_retries >= 1"
            )
        if bool(self.loop_cfg["coarse_center_enabled"]):
            required_center = set(CenteringConfig.__dataclass_fields__).union(
                {"stable_frames", "duration_ms"}
            )
            missing_center = sorted(required_center.difference(self.center_cfg))
            if missing_center:
                raise ValueError(
                    "visual_centering config missing: {}".format(
                        ", ".join(missing_center)
                    )
                )
            if int(self.center_cfg["yaw_servo_id"]) != 0:
                raise ValueError("COARSE_CENTER yaw_servo_id must be Servo000")
            if int(self.center_cfg["pitch_servo_id"]) != 3:
                raise ValueError("COARSE_CENTER pitch_servo_id must be Servo003")
            if int(self.loop_cfg["coarse_center_max_iterations"]) < 1:
                raise ValueError(
                    "coarse_center_max_iterations must be positive"
                )
            if int(self.center_cfg["stable_frames"]) < 1:
                raise ValueError("visual_centering stable_frames must be positive")
            if int(self.center_cfg["duration_ms"]) <= 0:
                raise ValueError("visual_centering duration_ms must be positive")

    def require_real_motion_calibration(self):
        """Call before opening a real motion path, never for seed-only observe."""

        failures = []
        if not self.frames.hand_eye_calibrated:
            failures.append("hand-eye calibrated=false")
        if not bool(
            self.config.get("hand_eye", {})
            .get("dynamic_validation", {})
            .get("accepted", False)
        ):
            failures.append("hand-eye dynamic_validation.accepted=false")
        if not self.frames.closed_calibrated:
            failures.append("closed TCP calibrated=false")
        if not bool(self.config.get("kinematics", {}).get("calibrated", False)):
            failures.append("kinematics calibrated=false")
        if not bool(self.config.get("serial", {}).get("joint_pwm_calibrated", False)):
            failures.append("serial joint_pwm_calibrated=false")
        if failures:
            raise ValueError("real motion calibration gate: " + "; ".join(failures))

    def require_real_close_calibration(self):
        """Reject CLOSE/LIFT until the physical gripper endpoints are accepted."""

        grasp = self.config.get("grasp", {})
        failures = []
        if not bool(grasp.get("gripper_open_calibrated", False)):
            failures.append("gripper open PWM/width calibrated=false")
        if not bool(grasp.get("gripper_close_calibrated", False)):
            failures.append("gripper safe close/contact PWM calibrated=false")
        if failures:
            raise ValueError("real close calibration gate: " + "; ".join(failures))

    @staticmethod
    def _depth_dict(depth):
        if depth is None:
            return None
        if hasattr(depth, "as_dict"):
            return depth.as_dict()
        if is_dataclass(depth):
            return asdict(depth)
        return dict(depth) if isinstance(depth, Mapping) else {"value": str(depth)}

    def _depth_value(self, depth) -> float:
        if depth is None:
            raise RecoverableObservationStop("depth observation missing")
        ok = getattr(depth, "ok", None)
        if ok is None and isinstance(depth, Mapping):
            ok = depth.get("ok")
        reason = getattr(depth, "reason", "")
        if isinstance(depth, Mapping):
            reason = depth.get("reason", reason)
        if ok is False:
            raise RecoverableObservationStop(
                "depth rejected: {}".format(reason or "quality gate")
            )
        value = getattr(depth, "depth_m", None)
        if value is None and isinstance(depth, Mapping):
            value = depth.get("depth_m")
        if value is None or not math.isfinite(float(value)) or float(value) <= 0.0:
            raise RecoverableObservationStop(
                "depth observation has no positive finite depth"
            )
        value = float(value)
        reliable_minimum = float(
            self.loop_cfg["minimum_reliable_aligned_depth_m"]
        )
        if value < reliable_minimum:
            raise RecoverableObservationStop(
                "aligned depth {:.3f} m is inside the measured D435 unreliable zone (< {:.3f} m)"
                .format(value, reliable_minimum)
            )
        return value

    def _transition(self, state: GraspState, detail: str = "", **extra):
        self.state = state
        row = {
            "wall_time": time.time(),
            "monotonic_time": time.monotonic(),
            "state": state.name,
            "iteration": self.approach_iterations,
            "track_id": self.track_id,
            "detail": detail,
        }
        row.update(extra)
        self.logger.log(row)

    def _fail(self, reason: str) -> ClosedLoopOutcome:
        self.stop_reason = str(reason)
        self._transition(GraspState.FAILED, stop_reason=self.stop_reason)
        return self.outcome(False, self.stop_reason)

    def outcome(self, ok: bool, reason: str = "") -> ClosedLoopOutcome:
        return ClosedLoopOutcome(
            ok=bool(ok),
            state=self.state,
            reason=str(reason),
            track_id=self.track_id,
            approach_iterations=self.approach_iterations,
            cumulative_approach_m=float(self.cumulative_approach_m),
            commands_executed=self.commands_executed,
            grasp_verification=self.grasp_verification,
        )

    def _next_observation(self, source, after_monotonic: float) -> DynamicObservation:
        observation = source.next_observation(
            after_monotonic=float(after_monotonic),
            expected_track_id=self.track_id,
        )
        if observation is None:
            raise RecoverableObservationStop(
                "target lost: observation source returned none"
            )
        if not isinstance(observation, DynamicObservation):
            raise TypeError("observation source must return DynamicObservation")
        if observation.acquired_monotonic <= float(after_monotonic):
            raise ClosedLoopStop(
                "stale RGB-D frame {:.6f} is not newer than {:.6f}".format(
                    observation.acquired_monotonic, after_monotonic
                )
            )
        if observation.acquired_monotonic <= self.last_frame_monotonic:
            raise ClosedLoopStop("RGB-D frame timestamp did not advance")
        age = time.monotonic() - observation.acquired_monotonic
        if age > float(self.loop_cfg["stale_frame_timeout_s"]):
            raise ClosedLoopStop("RGB-D frame is stale by {:.1f} ms".format(age * 1000.0))
        self.last_frame_monotonic = float(observation.acquired_monotonic)
        if observation.track_switched:
            raise ClosedLoopStop("target track switched: " + observation.association_reason)
        if observation.track_id is None or observation.bbox is None:
            raise RecoverableObservationStop(
                "target lost: " + observation.association_reason
            )
        if self.track_id is not None and observation.track_id != self.track_id:
            raise ClosedLoopStop(
                "target identity changed {} -> {}".format(
                    self.track_id, observation.track_id
                )
            )
        if not observation.track_stable:
            raise RecoverableObservationStop(
                "target association is not stable"
            )
        return observation

    def _fresh_context(self, source, require_gripper_pwm: bool = True) -> ObservationContext:
        # Required order for each approach iteration: measured PWM first, then
        # a new aligned RGB-D frame acquired after both the PWM snapshot and the
        # preceding motion completion barrier.
        snapshot = (
            self.arm.get_actual_pwm_snapshot()
            if require_gripper_pwm
            else self.arm.get_observation_pwm_snapshot()
        )
        barrier = max(
            float(self.last_motion_end_monotonic),
            float(snapshot.monotonic_timestamp),
            float(self.last_frame_monotonic),
        )
        observation = self._next_observation(source, barrier)
        if self.track_id is None:
            self.track_id = int(observation.track_id)
        depth_m = self._depth_value(observation.depth_observation)
        raw_pixel = observation.pixel_grasp_point or observation.bbox.center
        selected_pixel = apply_target_pixel_offset(
            raw_pixel, self.comp_cfg["target_pixel_offset_px"]
        )
        height, width = observation.image_shape_hw
        if not (0.0 <= selected_pixel[0] < width and 0.0 <= selected_pixel[1] < height):
            raise ClosedLoopStop("configured target pixel lies outside the RGB frame")
        raw_camera = depth_pixel_to_camera(
            selected_pixel, depth_m, observation.intrinsics
        )
        T_base_wrist = self.arm.kin.forward_wrist_matrix_from_pwm(
            snapshot.ordered((0, 1, 2, 3))
        )
        T_base_camera = self.frames.base_camera(T_base_wrist)
        T_base_tcp = self.frames.base_tcp(T_base_wrist, "closed")
        # final_insertion is a separate, post-FINAL_ALIGN action.  Never leak
        # it into ordinary observation, pregrasp or fine-approach targets.
        ordinary_compensation = dict(self.comp_cfg)
        ordinary_compensation["final_insertion_m"] = 0.0
        compensation = apply_grasp_compensation(
            raw_camera,
            T_base_camera,
            ordinary_compensation,
        )
        return ObservationContext(
            observation=observation,
            pwm_snapshot=snapshot,
            T_base_wrist=T_base_wrist,
            T_base_camera=T_base_camera,
            T_base_tcp_actual=T_base_tcp,
            selected_pixel=selected_pixel,
            raw_point_camera=raw_camera,
            compensation=compensation,
        )

    def _context_record(self, context: ObservationContext, **extra):
        obs = context.observation
        comp = context.compensation
        raw_pixel = (
            obs.pixel_grasp_point
            if obs.pixel_grasp_point is not None
            else (None if obs.bbox is None else obs.bbox.center)
        )
        raw_depth = (
            None
            if obs.depth_observation is None
            else getattr(obs.depth_observation, "depth_m", None)
        )
        row = {
            "wall_time": time.time(),
            "monotonic_time": time.monotonic(),
            "state": self.state.name,
            "iteration": self.approach_iterations,
            "track_id": self.track_id,
            "frame_timestamp": obs.frame_timestamp,
            "frame_monotonic": obs.acquired_monotonic,
            "frame_age_ms": (time.monotonic() - obs.acquired_monotonic) * 1000.0,
            "bbox": None if obs.bbox is None else asdict(obs.bbox),
            "raw_pixel": None if raw_pixel is None else list(raw_pixel),
            "raw_depth": raw_depth,
            "pixel_grasp_point": list(context.selected_pixel),
            "depth_observation": self._depth_dict(obs.depth_observation),
            "actual_pwms_000_005": [
                context.pwm_snapshot.pwms.get(servo_id) for servo_id in range(6)
            ],
            "missing_pwm_ids": [
                servo_id
                for servo_id in range(6)
                if servo_id not in context.pwm_snapshot.pwms
            ],
            "actual_joint_angles": list(
                self.arm.kin.pwm_to_joint_angles_deg(
                    context.pwm_snapshot.ordered((0, 1, 2, 3))
                )
            ),
            "T_base_wrist": context.T_base_wrist,
            "T_wrist_camera": self.frames.T_wrist_camera,
            "T_base_camera": context.T_base_camera,
            "T_wrist_tcp_active": self.frames.T_wrist_tcp_closed,
            "T_base_tcp_actual": context.T_base_tcp_actual,
            "raw_point_camera": comp.raw_point_camera,
            "corrected_point_camera": comp.corrected_point_camera,
            "raw_point_base_surface": comp.raw_point_base_surface,
            "object_center_point": comp.object_center_point,
            "local_approach_frame": comp.local_approach_frame,
            "object_grasp_point_base": comp.final_grasp_point_base,
            "final_grasp_point_base": comp.final_grasp_point_base,
            "applied_compensation": comp.applied_compensation,
            "compensation_snapshot": comp.applied_compensation,
        }
        if context.error_along_lateral_vertical is not None:
            row["error_along_lateral_vertical"] = list(
                context.error_along_lateral_vertical
            )
        row.update(extra)
        self.logger.log(row)

    def observe_once(
        self, source, require_gripper_pwm: bool = True
    ) -> ObservationContext:
        self._transition(GraspState.SEARCH, "waiting for stable tracked target")
        context = self._fresh_context(
            source, require_gripper_pwm=bool(require_gripper_pwm)
        )
        self._transition(GraspState.TRACK_STABLE, "same target stable")
        return self._depth_lock(
            source,
            context,
            detail="initial acquisition",
        )

    def _execute_motion(self, result: MotionResult, label: str):
        if not result.ok:
            raise ClosedLoopStop("{} failed: {}".format(label, result.reason))
        if not result.readback_reached:
            raise ClosedLoopStop("{} has no PRAD completion evidence".format(label))
        self.commands_executed += 1
        self.last_motion_end_monotonic = float(result.motion_end_monotonic)
        self.logger.log({
            "wall_time": time.time(),
            "monotonic_time": time.monotonic(),
            "state": self.state.name,
            "iteration": self.approach_iterations,
            "track_id": self.track_id,
            "motion_label": label,
            "command": result.command,
            "command_packed": result.command_packed,
            "command_written": result.command_written,
            "simulated": result.simulated,
            "readback_pwms": (
                None
                if result.readback_snapshot is None
                else list(result.readback_snapshot.ordered())
            ),
            "readback_mismatch": result.readback_mismatches,
            "motion_end_monotonic": result.motion_end_monotonic,
        })

    def _execute_plan(self, step: DynamicPlanStep):
        self.logger.log({
            "wall_time": time.time(),
            "monotonic_time": time.monotonic(),
            "state": step.state.name,
            "iteration": self.approach_iterations,
            "track_id": self.track_id,
            "planned_step_xyz": step.step_xyz_m,
            "planned_target_T_base_tcp": step.target_T_base_tcp,
            "commanded_pwms": step.servo_pwms,
            "ik_result": {
                "ok": True,
                "servo_pwms_000_003": list(step.ik.servo_pwms),
                "final_pitch_deg": step.ik.final_pitch_deg,
            },
        })
        self._execute_motion(
            self.arm.execute_assignments(
                {servo_id: int(pwm) for servo_id, pwm in enumerate(step.servo_pwms)},
                step.duration_ms,
                ik=step.ik,
            ),
            step.state.name,
        )

    def _safe_roi(self, context: ObservationContext) -> bool:
        margins = tuple(int(value) for value in self.loop_cfg["safe_roi_margin_px"])
        if len(margins) != 2 or min(margins) < 0:
            raise ValueError("safe_roi_margin_px must contain non-negative x/y")
        height, width = context.observation.image_shape_hw
        x, y = context.selected_pixel
        return bool(
            margins[0] <= x < width - margins[0]
            and margins[1] <= y < height - margins[1]
        )

    def _with_error(self, context: ObservationContext) -> ObservationContext:
        error = approach_error_along_lateral_vertical(
            context.T_base_tcp_actual,
            context.compensation.final_grasp_point_base,
            context.compensation.local_approach_frame[:3, 0],
        )
        return ObservationContext(
            observation=context.observation,
            pwm_snapshot=context.pwm_snapshot,
            T_base_wrist=context.T_base_wrist,
            T_base_camera=context.T_base_camera,
            T_base_tcp_actual=context.T_base_tcp_actual,
            selected_pixel=context.selected_pixel,
            raw_point_camera=context.raw_point_camera,
            compensation=context.compensation,
            error_along_lateral_vertical=error,
        )

    @staticmethod
    def _max_base_point_spread(points) -> float:
        values = np.asarray(points, dtype=float)
        if values.ndim != 2 or values.shape[1] != 3 or len(values) < 1:
            raise ValueError("base target points must be an N x 3 array")
        if not np.all(np.isfinite(values)):
            raise ClosedLoopStop("base target point contains non-finite values")
        deltas = values[:, None, :] - values[None, :, :]
        return float(np.max(np.linalg.norm(deltas, axis=2)))

    def _depth_lock(
        self,
        source,
        first_context: ObservationContext,
        detail: str = "initial acquisition",
    ) -> ObservationContext:
        """Require consecutive fresh image/PWM pairs with a stable base point."""

        required = int(self.loop_cfg["depth_lock_min_frames"])
        maximum_spread = float(
            self.loop_cfg["depth_lock_max_base_spread_m"]
        )
        points = []
        context = first_context
        self._transition(
            GraspState.DEPTH_LOCK,
            "{}: collecting consecutive fresh base targets".format(detail),
            depth_lock_frames_required=required,
            depth_lock_max_base_spread_m=maximum_spread,
        )
        for index in range(required):
            if index:
                context = self._fresh_context(source)
            point = np.asarray(
                context.compensation.final_grasp_point_base, dtype=float
            )
            if point.shape != (3,) or not np.all(np.isfinite(point)):
                raise ClosedLoopStop(
                    "base target point must contain three finite coordinates"
                )
            points.append(point.copy())
            spread = self._max_base_point_spread(points)
            self._context_record(
                context,
                depth_lock_candidate_index=index + 1,
                depth_lock_frames_required=required,
                base_target_spread_m=spread,
                base_target_spread_limit_m=maximum_spread,
            )
        spread = self._max_base_point_spread(points)
        if spread > maximum_spread:
            raise RecoverableObservationStop(
                "base target point unstable: spread {:.4f} m exceeds {:.4f} m"
                .format(spread, maximum_spread)
            )
        self._transition(
            GraspState.DEPTH_LOCK,
            "{}: base target stability accepted".format(detail),
            depth_lock_frames=required,
            base_target_spread_m=spread,
            base_target_spread_limit_m=maximum_spread,
        )
        return context

    def _coarse_center(
        self, source, first_context: ObservationContext
    ) -> ObservationContext:
        """Bounded image-space servo using only Servo000/003 assignments."""

        if not bool(self.loop_cfg["coarse_center_enabled"]):
            return first_context
        cfg_fields = {
            name: self.center_cfg[name]
            for name in CenteringConfig.__dataclass_fields__
        }
        centerer = PWMVisualCentering(CenteringConfig(**cfg_fields))
        stable_required = int(self.center_cfg["stable_frames"])
        max_motion_steps = int(
            self.loop_cfg["coarse_center_max_iterations"]
        )
        duration_ms = int(self.center_cfg["duration_ms"])
        context = first_context
        stable_count = 0
        motion_steps = 0
        self._transition(
            GraspState.COARSE_CENTER,
            "starting bounded bbox-centre visual servo",
            stable_frames_required=stable_required,
            max_motion_steps=max_motion_steps,
        )
        while True:
            observation = context.observation
            center_x, center_y = observation.bbox.center
            height, width = observation.image_shape_hw
            error_x = float(center_x - width / 2.0)
            error_y = float(center_y - height / 2.0)
            dead_zone = float(self.center_cfg["dead_zone_px"])
            aligned = (
                abs(error_x) <= dead_zone
                and abs(error_y) <= dead_zone
            )
            updates = centerer.command(
                observation.bbox,
                observation.image_shape_hw,
                context.pwm_snapshot.ordered(),
            )
            if any(servo_id not in (0, 3) for servo_id in updates):
                raise ClosedLoopStop(
                    "COARSE_CENTER attempted a non-Servo000/003 assignment"
                )
            self.logger.log({
                "wall_time": time.time(),
                "monotonic_time": time.monotonic(),
                "state": GraspState.COARSE_CENTER.name,
                "iteration": self.approach_iterations,
                "track_id": self.track_id,
                "frame_monotonic": observation.acquired_monotonic,
                "actual_pwms_000_005": list(
                    context.pwm_snapshot.ordered()
                ),
                "center_error_px": [error_x, error_y],
                "aligned": aligned,
                "stable_count": stable_count,
                "motion_steps": motion_steps,
                "requested_updates_000_003": dict(updates),
            })
            if aligned:
                stable_count += 1
                if stable_count >= stable_required:
                    return context
                context = self._fresh_context(source)
                continue
            stable_count = 0
            if not updates:
                raise ClosedLoopStop(
                    "COARSE_CENTER saturated outside the configured dead zone"
                )
            if motion_steps >= max_motion_steps:
                raise ClosedLoopStop(
                    "COARSE_CENTER maximum motion steps exceeded"
                )
            self._execute_motion(
                self.arm.execute_assignments(updates, duration_ms),
                "COARSE_CENTER",
            )
            motion_steps += 1
            # The command invalidates all older pixels and PWM values.
            context = self._fresh_context(source)

    def _plan_retry_backoff(
        self, safe_context: ObservationContext
    ) -> DynamicPlanStep:
        direction = np.asarray(
            safe_context.compensation.local_approach_frame[:3, 0],
            dtype=float,
        )
        norm = float(np.linalg.norm(direction))
        if direction.shape != (3,) or not math.isfinite(norm) or norm <= 1e-12:
            raise ClosedLoopStop(
                "retry backoff has no finite known-safe approach direction"
            )
        direction /= norm
        backoff_m = float(self.loop_cfg["retry_backoff_m"])
        actual_matrix, actual_snapshot = self._actual_tcp_for_planning()
        synthetic_retreat_target = (
            np.asarray(actual_matrix[:3, 3], dtype=float)
            - direction * backoff_m
        )
        candidate = plan_next_approach_step(
            actual_matrix,
            synthetic_retreat_target,
            direction,
            self.frames.T_wrist_tcp_closed,
            self.arm.kin,
            self.grasp_cfg,
            actual_snapshot.ordered(),
            max_step_m=backoff_m,
            min_step_m=0.005,
            close_distance_m=0.0,
            max_joint_pwm_step=int(self.loop_cfg["max_joint_pwm_step"]),
            duration_ms=int(self.grasp_cfg.retry_motion_ms),
            tcp_name="closed",
        )
        if candidate is None:
            raise ClosedLoopStop("retry backoff planner produced no motion")
        return DynamicPlanStep(
            state=GraspState.RETRY_BACKOFF,
            target_T_base_tcp=candidate.target_T_base_tcp,
            xyz_m=candidate.xyz_m,
            step_xyz_m=candidate.step_xyz_m,
            pitch_deg=candidate.pitch_deg,
            tcp_name=candidate.tcp_name,
            ik=candidate.ik,
            servo_pwms=candidate.servo_pwms,
            duration_ms=candidate.duration_ms,
        )

    def _recover_observation(
        self,
        source,
        failure: RecoverableObservationStop,
        safe_context: ObservationContext,
        retries_used: int,
    ):
        """Back off and reacquire only for explicitly recoverable failures."""

        if not isinstance(failure, RecoverableObservationStop):
            raise failure
        if not bool(self.loop_cfg["retry_backoff_enabled"]):
            raise failure
        maximum = int(self.loop_cfg["max_retries"])
        current_failure = failure
        while retries_used < maximum:
            retries_used += 1
            discarded_track_id = self.track_id
            direction = np.asarray(
                safe_context.compensation.local_approach_frame[:3, 0],
                dtype=float,
            )
            self._transition(
                GraspState.RETRY_BACKOFF,
                "recoverable target/depth failure; retreat before a new search",
                retry_index=retries_used,
                max_retries=maximum,
                recoverable_failure=str(current_failure),
                retry_backoff_m=float(self.loop_cfg["retry_backoff_m"]),
                known_safe_approach_direction=direction,
                discarded_track_id=discarded_track_id,
            )
            backoff = self._plan_retry_backoff(safe_context)
            self._execute_plan(backoff)
            # Do not carry identity or coordinates across the recovery move.
            self.track_id = None
            try:
                context = self.observe_once(source)
            except RecoverableObservationStop as exc:
                current_failure = exc
                continue
            return context, retries_used
        raise current_failure

    def _is_final_aligned(self, context: ObservationContext) -> bool:
        along, lateral, vertical = context.error_along_lateral_vertical
        close_distance = float(self.comp_cfg["close_distance_m"])
        tool_forward = context.T_base_tcp_actual[:3, 0]
        tool_pitch = math.degrees(
            math.asin(float(np.clip(tool_forward[2], -1.0, 1.0)))
        )
        horizontal_ok = (
            not bool(self.loop_cfg["final_motion_horizontal_only"])
            or abs(tool_pitch)
            <= float(self.loop_cfg["final_tool_pitch_tolerance_deg"])
        )
        return bool(
            abs(along - close_distance)
            <= float(self.loop_cfg["final_along_tolerance_m"])
            and abs(lateral)
            <= float(self.loop_cfg["final_lateral_tolerance_m"])
            and abs(vertical)
            <= float(self.loop_cfg["final_vertical_tolerance_m"])
            and self._safe_roi(context)
            and horizontal_ok
        )

    def _optional_fresh_context(self, source, label: str):
        try:
            return self._fresh_context(source), ""
        except Exception as exc:
            reason = "{} observation unavailable: {}".format(label, exc)
            self.logger.log({
                "wall_time": time.time(),
                "monotonic_time": time.monotonic(),
                "state": self.state.name,
                "iteration": self.approach_iterations,
                "track_id": self.track_id,
                "verification_observation_ok": False,
                "stop_reason": reason,
            })
            return None, reason

    def _verification_result(
        self,
        before: Optional[ObservationContext],
        after: Optional[ObservationContext],
        unavailable_reason: str = "",
    ) -> GraspVerification:
        if before is None or after is None:
            return GraspVerification(
                "uncertain",
                unavailable_reason or "verification RGB-D pair is incomplete",
                None,
                None,
                None,
            )
        before_camera = np.asarray(
            before.compensation.corrected_point_camera, dtype=float
        )
        after_camera = np.asarray(
            after.compensation.corrected_point_camera, dtype=float
        )
        before_base = np.asarray(
            before.compensation.final_grasp_point_base, dtype=float
        )
        after_base = np.asarray(
            after.compensation.final_grasp_point_base, dtype=float
        )
        camera_shift = float(np.linalg.norm(after_camera - before_camera))
        base_delta = after_base - before_base
        base_shift = float(np.linalg.norm(base_delta))
        vertical_shift = float(base_delta[2])
        expected_raise = float(self.loop_cfg["verify_lift_raise_m"])
        camera_tolerance = float(
            self.loop_cfg["verify_relative_camera_tolerance_m"]
        )
        table_tolerance = float(self.loop_cfg["verify_table_static_tolerance_m"])
        if (
            camera_shift <= camera_tolerance
            and vertical_shift >= max(0.003, expected_raise * 0.5)
        ):
            status = "grasp_verified"
            reason = "object stayed near camera/TCP and rose with the arm"
        elif base_shift <= table_tolerance and abs(vertical_shift) <= table_tolerance:
            status = "grasp_failed"
            reason = "object remained stationary in the base/table frame"
        else:
            status = "uncertain"
            reason = "verification evidence did not match held or table-static model"
        return GraspVerification(
            status,
            reason,
            camera_shift,
            base_shift,
            vertical_shift,
        )

    def _actual_tcp_for_planning(self):
        snapshot = self.arm.get_actual_pwm_snapshot()
        actual = self.arm.get_actual_tcp_pose(
            self.frames.T_wrist_tcp_closed,
            snapshot=snapshot,
            tcp_name="closed",
        )
        return actual.matrix, snapshot

    def _close_verify_and_lift(
        self,
        source,
        aligned_context: ObservationContext,
        requested: str,
    ) -> ClosedLoopOutcome:
        # This gate is deliberately before even the small final insertion:
        # an unmeasured close/contact endpoint must not authorize any extra
        # real motion beyond the already converged FINAL_ALIGN pose.
        if not self.arm.adapter.dry_run:
            self.require_real_close_calibration()
        insertion = plan_final_insertion(
            aligned_context.T_base_tcp_actual,
            aligned_context.compensation.local_approach_frame[:3, 0],
            float(self.comp_cfg["final_insertion_m"]),
            float(self.comp_cfg["max_final_insertion_m"]),
            self.frames.T_wrist_tcp_closed,
            self.arm.kin,
            self.grasp_cfg,
            aligned_context.pwm_snapshot.ordered(),
            tcp_name="closed",
            horizontal_only=bool(self.loop_cfg["final_motion_horizontal_only"]),
            max_tool_pitch_deg=float(
                self.loop_cfg["final_tool_pitch_tolerance_deg"]
            ),
        )
        if insertion is not None:
            self._transition(
                GraspState.FINAL_ALIGN,
                "executing configured post-convergence final insertion",
                final_insertion_m=float(self.comp_cfg["final_insertion_m"]),
            )
            self._execute_plan(insertion)

        self._transition(GraspState.CLOSE, "closing gripper independently of arm IK")
        close_result = self.arm.move_gripper(
            self.grasp_cfg.gripper_close_pwm,
            self.grasp_cfg.gripper_close_ms,
        )
        self._execute_motion(close_result, "CLOSE")
        self._transition(
            GraspState.VERIFY_CLOSE,
            "Servo005 PRAD confirms position only, not grasp success",
            servo005_readback=(
                None
                if close_result.readback_snapshot is None
                else close_result.readback_snapshot.pwms.get(5)
            ),
            grasp_success=False,
        )
        self.grasp_verification = "not_verified"

        before, before_reason = self._optional_fresh_context(
            source, "before verify-lift"
        )
        self._transition(
            GraspState.VERIFY_LIFT,
            "executing small verification raise before full lift",
        )
        actual_matrix, actual_snapshot = self._actual_tcp_for_planning()
        verify_step = plan_lift(
            actual_matrix,
            float(self.loop_cfg["verify_lift_raise_m"]),
            self.frames.T_wrist_tcp_closed,
            self.arm.kin,
            self.grasp_cfg,
            actual_snapshot.ordered(),
            duration_ms=self.grasp_cfg.verify_lift_ms,
            state=GraspState.VERIFY_LIFT,
            tcp_name="closed",
        )
        self._execute_plan(verify_step)
        after, after_reason = self._optional_fresh_context(
            source, "after verify-lift"
        )
        verification = self._verification_result(
            before,
            after,
            "; ".join(value for value in (before_reason, after_reason) if value),
        )
        self.grasp_verification = verification.status
        self.logger.log({
            "wall_time": time.time(),
            "monotonic_time": time.monotonic(),
            "state": GraspState.VERIFY_LIFT.name,
            "iteration": self.approach_iterations,
            "track_id": self.track_id,
            "grasp_verification": verification.as_dict(),
        })
        if verification.status == "grasp_failed":
            return self._fail("grasp_failed: " + verification.reason)
        continue_uncertain = bool(self.loop_cfg["uncertain_continue_to_full_lift"])
        if verification.status == "uncertain" and (
            requested == "close" or not continue_uncertain
        ):
            return self._fail("grasp verification uncertain: " + verification.reason)
        if requested == "close":
            self._transition(
                GraspState.DONE,
                "close and small verification lift complete; full lift not executed",
            )
            return self.outcome(
                True,
                "close complete and grasp verified; full lift not executed",
            )

        actual_matrix, actual_snapshot = self._actual_tcp_for_planning()
        remaining_lift = max(
            0.0,
            float(self.grasp_cfg.lift_raise_m)
            - float(self.loop_cfg["verify_lift_raise_m"]),
        )
        if remaining_lift > 0.0:
            full_lift = plan_lift(
                actual_matrix,
                remaining_lift,
                self.frames.T_wrist_tcp_closed,
                self.arm.kin,
                self.grasp_cfg,
                actual_snapshot.ordered(),
                duration_ms=self.grasp_cfg.lift_ms,
                state=GraspState.LIFT,
                tcp_name="closed",
                pitch_deg=self.grasp_cfg.lift_pitch_deg,
            )
            self._transition(GraspState.LIFT, "executing remaining verified lift")
            self._execute_plan(full_lift)
        self._transition(
            GraspState.DONE,
            "full lift complete with {} evidence".format(verification.status),
        )
        if verification.status == "uncertain":
            return self.outcome(
                False,
                "full lift executed by configured policy, but grasp remains uncertain",
            )
        return self.outcome(True, "lift complete and grasp verified")

    def run_to_stage(self, source, max_stage: str = "approach") -> ClosedLoopOutcome:
        requested = str(max_stage).strip().lower().replace("_", "")
        if requested not in ("pregrasp", "approach", "close", "lift"):
            raise ValueError("max_stage must be pregrasp, approach, close, or lift")
        try:
            if self.allow_motion and not self.arm.adapter.dry_run:
                self.require_real_motion_calibration()
            self._transition(GraspState.INIT, "dynamic transform and safety config loaded")
            context = self.observe_once(source)
            if not self.allow_motion:
                raise ClosedLoopStop("motion stage requested while allow_motion=false")

            self._transition(GraspState.PLAN_PREGRASP, "opening gripper independently")
            self._execute_motion(
                self.arm.move_gripper(
                    self.grasp_cfg.gripper_open_pwm,
                    self.grasp_cfg.gripper_open_ms,
                ),
                "OPEN",
            )
            # Opening is a motion too.  Discard older frames and pair a new
            # observation with a new six-axis PRAD snapshot before planning.
            context = self._fresh_context(source)
            current_pwms = context.pwm_snapshot.ordered()
            pregrasp = plan_pregrasp(
                context.T_base_tcp_actual,
                context.compensation.final_grasp_point_base,
                context.compensation.local_approach_frame[:3, 0],
                self.frames.T_wrist_tcp_closed,
                self.arm.kin,
                self.grasp_cfg,
                current_pwms,
                standoff_m=float(self.comp_cfg["pregrasp_standoff_m"]),
                tcp_name="closed",
            )
            self._transition(GraspState.MOVE_PREGRASP, "executing only pregrasp")
            self._execute_plan(pregrasp)

            self._transition(
                GraspState.REACQUIRE_AFTER_PREGRASP,
                "old target coordinates invalidated",
            )
            context = self._with_error(self._fresh_context(source))
            self._context_record(context, reacquired_after_motion=True)
            if requested == "pregrasp":
                self._transition(GraspState.DONE, "pregrasp held after fresh reacquisition")
                return self.outcome(True, "pregrasp complete")

            self._transition(GraspState.FINE_APPROACH, "starting one-step feedback loop")
            approach_started = time.monotonic()
            stable_count = 0
            while True:
                if time.monotonic() - approach_started > float(
                    self.loop_cfg["max_approach_time_s"]
                ):
                    raise ClosedLoopStop("maximum approach time exceeded")
                context = self._with_error(context)
                aligned = self._is_final_aligned(context)
                stable_count = stable_count + 1 if aligned else 0
                self._context_record(
                    context,
                    final_align_candidate=aligned,
                    final_align_stable_count=stable_count,
                )
                if stable_count >= int(self.loop_cfg["final_align_stable_frames"]):
                    self._transition(
                        GraspState.FINAL_ALIGN,
                        "fresh observations converged",
                    )
                    if requested == "approach":
                        self._transition(
                            GraspState.DONE,
                            "approach stage complete; no close command issued",
                        )
                        return self.outcome(True, "final align complete")
                    return self._close_verify_and_lift(
                        source, context, requested
                    )

                if aligned:
                    # Require another independently timestamped image/PWM pair.
                    context = self._fresh_context(source)
                    continue
                if self.approach_iterations >= int(
                    self.loop_cfg["max_approach_iterations"]
                ):
                    raise ClosedLoopStop("maximum approach iterations exceeded")
                step = plan_next_approach_step(
                    context.T_base_tcp_actual,
                    context.compensation.final_grasp_point_base,
                    context.compensation.local_approach_frame[:3, 0],
                    self.frames.T_wrist_tcp_closed,
                    self.arm.kin,
                    self.grasp_cfg,
                    context.pwm_snapshot.ordered(),
                    max_step_m=float(self.comp_cfg["approach_step_m"]),
                    min_step_m=float(self.comp_cfg["min_approach_step_m"]),
                    close_distance_m=float(self.comp_cfg["close_distance_m"]),
                    max_joint_pwm_step=int(self.loop_cfg["max_joint_pwm_step"]),
                    tcp_name="closed",
                )
                if step is None:
                    raise ClosedLoopStop(
                        "remaining correction is below 5 mm but FINAL_ALIGN gates are not met"
                    )
                step_length = float(np.linalg.norm(step.step_xyz_m))
                next_cumulative = self.cumulative_approach_m + step_length
                if next_cumulative > float(self.loop_cfg["max_cumulative_approach_m"]):
                    raise ClosedLoopStop("maximum cumulative approach distance exceeded")
                self.approach_iterations += 1
                self._execute_plan(step)
                self.cumulative_approach_m = next_cumulative
                # No cached target survives this command.
                context = self._fresh_context(source)
        except Exception as exc:
            return self._fail(str(exc))


# Dynamic is the default public state machine.  The old implementation remains
# available only through the explicit legacy runtime module/CLI mode.
GraspStateMachine = DynamicGraspStateMachine
