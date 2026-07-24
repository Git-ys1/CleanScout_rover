# coding: utf-8
"""Pure fixed-view grasp planning with no camera or serial side effects."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
import math
from typing import Mapping, Optional, Sequence, Tuple

import numpy as np

from .fixed_view import (
    REQUIRED_WRIST_PWM,
    cartesian_line_points,
    horizontal_approach_axis,
    pre_grasp_from_bottle_center,
)
from .geometry import approach_frame_matrix, validate_rigid_transform


class GraspState(Enum):
    INIT = auto()
    SEARCH = auto()
    TRACK_STABLE = auto()
    COARSE_CENTER = auto()
    CENTERING = auto()
    DEPTH_LOCK = auto()
    PLAN_PREGRASP = auto()
    MOVE_PREGRASP = auto()
    REACQUIRE_AFTER_PREGRASP = auto()
    FINE_APPROACH = auto()
    FINAL_ALIGN = auto()
    WRIST_LOCK = auto()
    OPEN = auto()
    PRE_GRASP = auto()
    APPROACH = auto()
    CLOSE = auto()
    VERIFY_CLOSE = auto()
    VERIFY_LIFT = auto()
    LIFT = auto()
    DONE = auto()
    RETRY_BACKOFF = auto()
    RETURN_VERIFY = auto()
    VERIFY = auto()
    RETRY = auto()
    FAILED = auto()


@dataclass
class GraspConfig:
    stable_frames: int = 5
    max_center_jitter_px: float = 10.0
    depth_stable_frames: int = 4
    max_depth_jitter_m: float = 0.025
    depth_roi_inner_ratio: float = 0.35
    pre_grasp_standoff_m: float = 0.070
    approach_waypoint_spacing_m: float = 0.010
    approach_waypoint_ms: int = 450
    lift_raise_m: float = 0.080
    pitch_deg: float = 0.0
    pregrasp_pitch_deg: float = 0.0
    approach_pitch_deg: float = 0.0
    lift_pitch_deg: float = -11.0
    gripper_open_pwm: int = 1112
    gripper_close_pwm: int = 2000
    wrist_fixed_pwm: int = REQUIRED_WRIST_PWM
    wrist_lock_ms: int = 1000
    gripper_open_ms: int = 2000
    pre_grasp_ms: int = 1800
    gripper_close_ms: int = 1800
    verify_lift_ms: int = 900
    lift_ms: int = 1800
    retry_motion_ms: int = 3500
    retry_pose_pwms: Tuple[int, int, int, int, int, int] = (1500, 1909, 1900, 620, 1500, 1500)
    servo_pwm_limits: Tuple[Tuple[int, int], ...] = (
        (767, 2233), (767, 2233), (1500, 2490),
        (500, 2233), (REQUIRED_WRIST_PWM, REQUIRED_WRIST_PWM), (1000, 2200),
    )
    workspace_min_xyz_m: Tuple[float, float, float] = (0.04, -0.30, 0.015)
    workspace_max_xyz_m: Tuple[float, float, float] = (0.39, 0.30, 0.42)
    motion_settle_s: float = 0.15

    @classmethod
    def from_mapping(cls, mapping):
        required = set(cls.__dataclass_fields__.keys())
        missing = sorted(required.difference(mapping))
        if missing:
            raise ValueError("grasp config missing fields: " + ", ".join(missing))
        return cls(**{name: mapping[name] for name in required})


@dataclass(frozen=True)
class GraspPlanStep:
    state: GraspState
    xyz_m: Optional[Tuple[float, float, float]]
    pitch_deg: Optional[float]
    gripper_pwm: int
    duration_ms: int
    ik: Optional[object]
    servo_pwms: Tuple[int, int, int, int, int, int]
    waypoint_index: int = 1
    waypoint_count: int = 1
    workspace_ok: Optional[bool] = True
    ik_ok: Optional[bool] = True
    pwm_ok: Optional[bool] = True

    def as_dict(self):
        joints = None if self.ik is None else [float(value) for value in self.ik.joints_rad]
        angles = None if self.ik is None else [float(value) for value in self.ik.servo_angles_deg]
        return {
            "state": self.state.name,
            "waypoint_index": int(self.waypoint_index),
            "waypoint_count": int(self.waypoint_count),
            "xyz_m": None if self.xyz_m is None else [float(value) for value in self.xyz_m],
            "pitch_deg": None if self.pitch_deg is None else float(self.pitch_deg),
            "joints_rad": joints,
            "servo_angles_deg": angles,
            "servo_pwms_000_005": [int(value) for value in self.servo_pwms],
            "gripper_pwm_005": int(self.gripper_pwm),
            "duration_ms": int(self.duration_ms),
            "workspace_ok": None if self.workspace_ok is None else bool(self.workspace_ok),
            "ik_ok": None if self.ik_ok is None else bool(self.ik_ok),
            "pwm_ok": None if self.pwm_ok is None else bool(self.pwm_ok),
        }


@dataclass(frozen=True)
class DynamicPlanStep:
    """Exactly one motion that may be executed after its current observation."""

    state: GraspState
    target_T_base_tcp: np.ndarray
    xyz_m: Tuple[float, float, float]
    step_xyz_m: Tuple[float, float, float]
    pitch_deg: float
    tcp_name: str
    ik: object
    servo_pwms: Tuple[int, int, int, int, int, int]
    duration_ms: int

    def __post_init__(self):
        matrix = validate_rigid_transform(
            self.target_T_base_tcp, "target_T_base_tcp"
        ).copy()
        matrix.setflags(write=False)
        object.__setattr__(self, "target_T_base_tcp", matrix)

    def as_dict(self):
        return {
            "state": self.state.name,
            "target_T_base_tcp": self.target_T_base_tcp.tolist(),
            "xyz_m": [float(value) for value in self.xyz_m],
            "step_xyz_m": [float(value) for value in self.step_xyz_m],
            "step_norm_m": float(np.linalg.norm(self.step_xyz_m)),
            "pitch_deg": float(self.pitch_deg),
            "tcp_name": self.tcp_name,
            "servo_pwms_000_005": [int(value) for value in self.servo_pwms],
            "duration_ms": int(self.duration_ms),
        }


def inside_workspace(xyz_m, config: GraspConfig) -> bool:
    xyz = np.asarray(xyz_m, dtype=float)
    low = np.asarray(config.workspace_min_xyz_m, dtype=float)
    high = np.asarray(config.workspace_max_xyz_m, dtype=float)
    return bool(xyz.shape == (3,) and np.all(np.isfinite(xyz))
                and np.all(xyz >= low) and np.all(xyz <= high))


def validate_servo_pwms(servo_pwms, config: GraspConfig):
    values = tuple(int(value) for value in servo_pwms)
    limits = tuple(tuple(int(bound) for bound in pair) for pair in config.servo_pwm_limits)
    if len(values) != 6 or len(limits) != 6 or any(len(pair) != 2 for pair in limits):
        raise ValueError("servo PWM values and limits must each contain six entries")
    for servo_id, (value, bounds) in enumerate(zip(values, limits)):
        low, high = bounds
        if low > high or value < low or value > high:
            raise ValueError(
                "Servo{:03d} PWM {} outside measured bounds {}..{}".format(
                    servo_id, value, low, high
                )
            )
    if values[4] != REQUIRED_WRIST_PWM:
        raise ValueError("Servo004 must remain fixed at PWM {}".format(REQUIRED_WRIST_PWM))
    return values


def _dynamic_step(
    state: GraspState,
    target_T_base_tcp,
    current_T_base_tcp,
    T_wrist_tcp,
    kinematics,
    config: GraspConfig,
    current_pwms: Sequence[int],
    duration_ms: int,
    tcp_name: str = "closed",
    max_joint_pwm_step: Optional[int] = None,
) -> DynamicPlanStep:
    target = validate_rigid_transform(target_T_base_tcp, "target_T_base_tcp")
    current = validate_rigid_transform(current_T_base_tcp, "current_T_base_tcp")
    actual = tuple(int(value) for value in current_pwms)
    if len(actual) != 6:
        raise ValueError("current_pwms must contain Servo000..005")
    validate_servo_pwms(actual, config)
    if not inside_workspace(target[:3, 3], config):
        raise ValueError(
            "{} TCP target outside workspace: {}".format(
                state.name, target[:3, 3].tolist()
            )
        )
    ik = kinematics.inverse_tcp_pose(
        target_T_base_tcp=target,
        T_wrist_tcp=T_wrist_tcp,
        tcp_name=tcp_name,
    )
    if ik is None:
        raise ValueError(
            "{} target has no TCP IK solution: {}".format(
                state.name, target[:3, 3].tolist()
            )
        )
    arm_pwms = tuple(int(value) for value in ik.servo_pwms)
    if len(arm_pwms) != 4:
        raise ValueError("TCP IK must provide Servo000..003 PWM values")
    full_pwms = validate_servo_pwms(
        arm_pwms + (int(config.wrist_fixed_pwm), actual[5]), config
    )
    if max_joint_pwm_step is not None:
        bound = int(max_joint_pwm_step)
        if bound <= 0:
            raise ValueError("max_joint_pwm_step must be positive")
        deltas = [abs(full_pwms[index] - actual[index]) for index in range(4)]
        if max(deltas) > bound:
            raise ValueError(
                "{} joint PWM step {} exceeds configured maximum {}: {}".format(
                    state.name, max(deltas), bound, deltas
                )
            )
    delta = target[:3, 3] - current[:3, 3]
    return DynamicPlanStep(
        state=state,
        target_T_base_tcp=target,
        xyz_m=tuple(float(value) for value in target[:3, 3]),
        step_xyz_m=tuple(float(value) for value in delta),
        pitch_deg=float(ik.final_pitch_deg),
        tcp_name=str(tcp_name),
        ik=ik,
        servo_pwms=full_pwms,
        duration_ms=int(duration_ms),
    )


def _tcp_pose_with_pitch(xyz_m, approach_direction_base, pitch_deg):
    xyz = np.asarray(xyz_m, dtype=float)
    direction = np.asarray(approach_direction_base, dtype=float)
    if xyz.shape != (3,) or direction.shape != (3,):
        raise ValueError("TCP xyz and approach direction must contain three values")
    horizontal = float(math.hypot(xyz[0], xyz[1]))
    if not np.all(np.isfinite(direction)) or float(np.linalg.norm(direction)) <= 1e-12:
        raise ValueError("approach direction must have a horizontal component")
    if horizontal <= 1e-12:
        raise ValueError("TCP target must not lie on the base yaw axis")
    # This arm has one base-yaw DOF: the tool X axis must remain in the radial
    # plane through the requested TCP.  The Cartesian correction may follow a
    # camera-ray approach direction, but yaw cannot independently point there.
    phi = math.atan2(float(xyz[1]), float(xyz[0]))
    alpha = math.radians(-float(pitch_deg))
    x_axis = np.array(
        [math.cos(alpha) * math.cos(phi), math.cos(alpha) * math.sin(phi), math.sin(alpha)]
    )
    y_axis = np.array([-math.sin(phi), math.cos(phi), 0.0])
    z_axis = np.cross(x_axis, y_axis)
    matrix = np.eye(4, dtype=float)
    matrix[:3, :3] = np.column_stack((x_axis, y_axis, z_axis))
    matrix[:3, 3] = xyz
    return validate_rigid_transform(matrix, "target_T_base_tcp")


def plan_pregrasp(
    current_T_base_tcp,
    grasp_point_base_m,
    approach_direction_base,
    T_wrist_tcp,
    kinematics,
    config: GraspConfig,
    current_pwms: Sequence[int],
    standoff_m: float,
    duration_ms: Optional[int] = None,
    tcp_name: str = "closed",
) -> DynamicPlanStep:
    """Plan only the safe intermediate observation pose."""

    standoff = float(standoff_m)
    if not math.isfinite(standoff) or standoff <= 0.0:
        raise ValueError("pregrasp standoff must be positive")
    approach = approach_frame_matrix(
        grasp_point_base_m, approach_direction_base
    )
    target_xyz = (
        np.asarray(grasp_point_base_m, dtype=float)
        - approach[:3, 0] * standoff
    )
    target = _tcp_pose_with_pitch(
        target_xyz, approach_direction_base, config.pregrasp_pitch_deg
    )
    return _dynamic_step(
        GraspState.MOVE_PREGRASP,
        target,
        current_T_base_tcp,
        T_wrist_tcp,
        kinematics,
        config,
        current_pwms,
        config.pre_grasp_ms if duration_ms is None else int(duration_ms),
        tcp_name=tcp_name,
    )


def approach_error_along_lateral_vertical(
    current_T_base_tcp, grasp_point_base_m, approach_direction_base
) -> Tuple[float, float, float]:
    current = validate_rigid_transform(current_T_base_tcp, "current_T_base_tcp")
    frame = approach_frame_matrix(grasp_point_base_m, approach_direction_base)
    error_base = np.asarray(grasp_point_base_m, dtype=float) - current[:3, 3]
    error_local = frame[:3, :3].T @ error_base
    return tuple(float(value) for value in error_local)


def plan_next_approach_step(
    current_T_base_tcp,
    grasp_point_base_m,
    approach_direction_base,
    T_wrist_tcp,
    kinematics,
    config: GraspConfig,
    current_pwms: Sequence[int],
    max_step_m: float,
    min_step_m: float,
    close_distance_m: float,
    max_joint_pwm_step: int,
    duration_ms: Optional[int] = None,
    tcp_name: str = "closed",
) -> Optional[DynamicPlanStep]:
    """Plan one 5--10 mm correction from the current measured TCP.

    ``None`` means the TCP is already within one minimum step of the desired
    close-distance plane; FINAL_ALIGN must decide whether it is truly stable.
    No list of future waypoints is ever generated.
    """

    current = validate_rigid_transform(current_T_base_tcp, "current_T_base_tcp")
    minimum = float(min_step_m)
    maximum = float(max_step_m)
    close_distance = float(close_distance_m)
    if not (0.005 <= minimum <= maximum <= 0.010):
        raise ValueError("approach steps must satisfy 0.005 <= min <= max <= 0.010 m")
    if close_distance < 0.0 or not math.isfinite(close_distance):
        raise ValueError("close_distance_m must be finite and non-negative")
    approach = approach_frame_matrix(
        grasp_point_base_m, approach_direction_base
    )
    desired_xyz = (
        np.asarray(grasp_point_base_m, dtype=float)
        - approach[:3, 0] * close_distance
    )
    remaining = desired_xyz - current[:3, 3]
    distance = float(np.linalg.norm(remaining))
    if distance < minimum:
        return None
    step_length = min(maximum, distance)
    step = remaining / distance * step_length
    target = _tcp_pose_with_pitch(
        current[:3, 3] + step,
        approach_direction_base,
        config.approach_pitch_deg,
    )
    return _dynamic_step(
        GraspState.FINE_APPROACH,
        target,
        current,
        T_wrist_tcp,
        kinematics,
        config,
        current_pwms,
        config.approach_waypoint_ms if duration_ms is None else int(duration_ms),
        tcp_name=tcp_name,
        max_joint_pwm_step=max_joint_pwm_step,
    )


def plan_final_insertion(
    current_T_base_tcp,
    approach_direction_base,
    insertion_m: float,
    max_insertion_m: float,
    T_wrist_tcp,
    kinematics,
    config: GraspConfig,
    current_pwms: Sequence[int],
    duration_ms: Optional[int] = None,
    tcp_name: str = "closed",
    horizontal_only: bool = True,
    max_tool_pitch_deg: float = 2.0,
) -> Optional[DynamicPlanStep]:
    """Plan the optional blind insertion allowed only after FINAL_ALIGN."""

    insertion = float(insertion_m)
    maximum = float(max_insertion_m)
    if insertion < 0.0 or maximum < 0.0 or insertion > maximum:
        raise ValueError("final insertion must be in 0..max_final_insertion_m")
    if insertion == 0.0:
        return None
    current = validate_rigid_transform(current_T_base_tcp, "current_T_base_tcp")
    observed_direction = np.asarray(approach_direction_base, dtype=float)
    norm = float(np.linalg.norm(observed_direction))
    if observed_direction.shape != (3,) or not math.isfinite(norm) or norm <= 1e-12:
        raise ValueError("approach_direction_base must be a finite nonzero vector")
    if horizontal_only:
        tool_forward = current[:3, 0].copy()
        tool_pitch = math.degrees(math.asin(float(np.clip(tool_forward[2], -1.0, 1.0))))
        if abs(tool_pitch) > float(max_tool_pitch_deg):
            raise ValueError(
                "final insertion requires a horizontal tool; measured pitch {:.3f} deg"
                .format(tool_pitch)
            )
        direction = np.array([tool_forward[0], tool_forward[1], 0.0], dtype=float)
        direction /= np.linalg.norm(direction)
        observed_horizontal = observed_direction.copy()
        observed_horizontal[2] = 0.0
        observed_norm = float(np.linalg.norm(observed_horizontal))
        if observed_norm > 1e-12 and float(
            np.dot(direction, observed_horizontal / observed_norm)
        ) <= 0.0:
            raise ValueError("tool forward points away from the observed target")
    else:
        direction = observed_direction / norm
    target = current.copy()
    target[:3, 3] += direction * insertion
    if horizontal_only and not math.isclose(
        float(target[2, 3]), float(current[2, 3]), rel_tol=0.0, abs_tol=1e-12
    ):
        raise AssertionError("horizontal final insertion changed base Z")
    return _dynamic_step(
        GraspState.FINAL_ALIGN,
        target,
        current,
        T_wrist_tcp,
        kinematics,
        config,
        current_pwms,
        config.approach_waypoint_ms if duration_ms is None else int(duration_ms),
        tcp_name=tcp_name,
        max_joint_pwm_step=None,
    )


def plan_lift(
    current_T_base_tcp,
    lift_m: float,
    T_wrist_tcp,
    kinematics,
    config: GraspConfig,
    current_pwms: Sequence[int],
    duration_ms: Optional[int] = None,
    state: GraspState = GraspState.LIFT,
    tcp_name: str = "closed",
    pitch_deg: Optional[float] = None,
) -> DynamicPlanStep:
    raise_distance = float(lift_m)
    if raise_distance <= 0.0 or not math.isfinite(raise_distance):
        raise ValueError("lift distance must be positive")
    current = validate_rigid_transform(current_T_base_tcp, "current_T_base_tcp")
    target_xyz = current[:3, 3].copy()
    target_xyz[2] += raise_distance
    if pitch_deg is None:
        target = current.copy()
        target[:3, 3] = target_xyz
    else:
        target = _tcp_pose_with_pitch(
            target_xyz, target_xyz, float(pitch_deg)
        )
    return _dynamic_step(
        state,
        target,
        current,
        T_wrist_tcp,
        kinematics,
        config,
        current_pwms,
        config.lift_ms if duration_ms is None else int(duration_ms),
        tcp_name=tcp_name,
    )


def _motion_step(state, xyz_m, pitch_deg, gripper_pwm, duration_ms,
                 kinematics, config, waypoint_index=1, waypoint_count=1):
    xyz = np.asarray(xyz_m, dtype=float)
    if not inside_workspace(xyz, config):
        raise ValueError("{} target outside workspace: {}".format(state.name, xyz.tolist()))
    ik = kinematics.inverse_pose(xyz, pitch_deg=float(pitch_deg), gripper=0.0)
    if ik is None:
        raise ValueError("{} target has no IK solution: {}".format(state.name, xyz.tolist()))
    arm_pwms = tuple(int(value) for value in getattr(ik, "servo_pwms", ()))
    if len(arm_pwms) != 4:
        raise ValueError("{} IK must provide Servo000..003 PWM values".format(state.name))
    full_pwms = validate_servo_pwms(
        arm_pwms + (int(config.wrist_fixed_pwm), int(gripper_pwm)), config
    )
    return GraspPlanStep(
        state=state,
        xyz_m=tuple(float(value) for value in xyz),
        pitch_deg=float(pitch_deg),
        gripper_pwm=int(gripper_pwm),
        duration_ms=int(duration_ms),
        ik=ik,
        servo_pwms=full_pwms,
        waypoint_index=int(waypoint_index),
        waypoint_count=int(waypoint_count),
    )


def build_fixed_view_grasp_plan(bottle_center_base_m, kinematics,
                                config: GraspConfig, max_stage=None):
    """Build OPEN/PRE_GRASP/APPROACH/CLOSE/LIFT with full preflight checks."""
    requested_stage = None if max_stage is None else str(max_stage).strip().upper()
    allowed_stages = {"OPEN", "PRE_GRASP", "APPROACH", "CLOSE", "LIFT"}
    if requested_stage is not None and requested_stage not in allowed_stages:
        raise ValueError("max_stage must be one of {}".format(sorted(allowed_stages)))
    if not 0.060 <= float(config.pre_grasp_standoff_m) <= 0.080:
        raise ValueError("pre_grasp_standoff_m must be in 0.060..0.080 m")
    if int(config.wrist_fixed_pwm) != REQUIRED_WRIST_PWM:
        raise ValueError("Servo004 must remain fixed at PWM {}".format(REQUIRED_WRIST_PWM))
    reference = tuple(int(value) for value in config.retry_pose_pwms)
    if len(reference) != 6 or reference[4] != REQUIRED_WRIST_PWM:
        raise ValueError("reference pose must contain six PWM values with Servo004={}".format(
            REQUIRED_WRIST_PWM
        ))

    open_pwms = list(reference)
    open_pwms[4] = REQUIRED_WRIST_PWM
    open_pwms[5] = int(config.gripper_open_pwm)
    open_step = GraspPlanStep(
        state=GraspState.OPEN,
        xyz_m=None,
        pitch_deg=None,
        gripper_pwm=int(config.gripper_open_pwm),
        duration_ms=int(config.gripper_open_ms),
        ik=None,
        servo_pwms=validate_servo_pwms(open_pwms, config),
        workspace_ok=None,
        ik_ok=None,
    )

    if requested_stage == "OPEN":
        return [open_step]

    center = np.asarray(bottle_center_base_m, dtype=float)
    if center.shape != (3,) or not np.all(np.isfinite(center)):
        raise ValueError("bottle center must contain three finite base-frame values")
    pre = pre_grasp_from_bottle_center(center, config.pre_grasp_standoff_m)
    approach = center.copy()
    if abs(float(pre[2] - approach[2])) > 1e-9:
        raise ValueError("fixed-view approach must remain horizontal")

    steps = [open_step]
    steps.append(_motion_step(
        GraspState.PRE_GRASP, pre, config.pitch_deg, config.gripper_open_pwm,
        config.pre_grasp_ms, kinematics, config,
    ))
    if requested_stage == "PRE_GRASP":
        return steps
    waypoints = cartesian_line_points(pre, approach, config.approach_waypoint_spacing_m)
    for index, waypoint in enumerate(waypoints, start=1):
        steps.append(_motion_step(
            GraspState.APPROACH, waypoint, config.pitch_deg, config.gripper_open_pwm,
            config.approach_waypoint_ms, kinematics, config,
            waypoint_index=index, waypoint_count=len(waypoints),
        ))
    if requested_stage == "APPROACH":
        return steps
    steps.append(_motion_step(
        GraspState.CLOSE, approach, config.pitch_deg, config.gripper_close_pwm,
        config.gripper_close_ms, kinematics, config,
    ))
    if requested_stage == "CLOSE":
        return steps
    lift = approach.copy()
    lift[2] += float(config.lift_raise_m)
    steps.append(_motion_step(
        GraspState.LIFT, lift, config.lift_pitch_deg, config.gripper_close_pwm,
        config.lift_ms, kinematics, config,
    ))
    return steps


def stage_reached(current_state: GraspState, next_state: Optional[GraspState], max_stage):
    target = str(max_stage).strip().upper()
    if current_state.name != target:
        return False
    return next_state is None or next_state != current_state
