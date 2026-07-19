# coding: utf-8
"""Pure fixed-view grasp planning with no camera or serial side effects."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
import math
from typing import Optional, Tuple

import numpy as np

from .fixed_view import (
    REQUIRED_WRIST_PWM,
    cartesian_line_points,
    horizontal_approach_axis,
    pre_grasp_from_bottle_center,
)


class GraspState(Enum):
    SEARCH = auto()
    CENTERING = auto()
    DEPTH_LOCK = auto()
    WRIST_LOCK = auto()
    OPEN = auto()
    PRE_GRASP = auto()
    APPROACH = auto()
    CLOSE = auto()
    LIFT = auto()
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
    lift_pitch_deg: float = -11.0
    gripper_open_pwm: int = 1000
    gripper_close_pwm: int = 2000
    wrist_fixed_pwm: int = REQUIRED_WRIST_PWM
    wrist_lock_ms: int = 1000
    gripper_open_ms: int = 2000
    pre_grasp_ms: int = 1800
    gripper_close_ms: int = 1800
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
