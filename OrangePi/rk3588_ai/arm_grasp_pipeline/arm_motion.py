# coding: utf-8
"""High-level arm motion: base xyz -> IK -> RF1 serial text protocol."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Sequence

import numpy as np

from .kinematics_5dof import Arm5DoFKinematics, IKResult
from .serial_servo_adapter import SerialServoArmAdapter


@dataclass
class MotionResult:
    ok: bool
    ik: Optional[IKResult]
    command: str = ""
    reason: str = ""


class ArmMotion:
    def __init__(
        self,
        adapter: SerialServoArmAdapter,
        kinematics=None,
        current_joints_rad: Optional[Sequence[float]] = None,
        reference_ee_matrix: Optional[np.ndarray] = None,
    ) -> None:
        self.adapter = adapter
        self.kin = kinematics or Arm5DoFKinematics()
        self.last_ik: Optional[IKResult] = None
        self.current_joints_rad = list(current_joints_rad or [0.0, -0.93, 1.6, 1.2, 0.0, 0.801])
        self.reference_ee_matrix = None if reference_ee_matrix is None else np.asarray(reference_ee_matrix, dtype=float)

    def current_ee_matrix_from_last_command(self) -> np.ndarray:
        if self.last_ik is not None and getattr(self.last_ik, "tool_matrix", None) is not None:
            return np.asarray(self.last_ik.tool_matrix, dtype=float).copy()
        if self.last_ik is None and self.reference_ee_matrix is not None:
            return self.reference_ee_matrix.copy()
        if self.last_ik is None:
            return self.kin.forward_matrix(self.current_joints_rad[:5])
        return self.kin.forward_matrix(self.last_ik.joints_rad[:5])

    def pack_ik_command(self, ik, duration_ms: int, gripper_pwm: Optional[int] = None,
                        include_gripper: bool = True) -> str:
        servo_pwms = getattr(ik, "servo_pwms", None)
        if servo_pwms is not None:
            values = list(servo_pwms)
            if gripper_pwm is not None:
                values[5] = int(gripper_pwm)
            if include_gripper:
                return self.adapter.pack_pwm_command(values, duration_ms)
            return self.adapter.pack_partial_pwm_command(dict(enumerate(values[:5])), duration_ms)
        if include_gripper:
            return self.adapter.pack_joint_command(ik.joints_rad, duration_ms)
        assignments = {
            mapping.servo_id: mapping.to_pwm(rad)
            for rad, mapping in zip(ik.joints_rad[:5], self.adapter.joint_maps[:5])
        }
        return self.adapter.pack_partial_pwm_command(assignments, duration_ms)

    def set_reference_ee_matrix(self, matrix: np.ndarray) -> None:
        self.reference_ee_matrix = np.asarray(matrix, dtype=float).copy()
        self.last_ik = None

    def move_xyz(self, xyz_m: Iterable[float], pitch_deg: float = 70.0, roll_rad: float = -0.05,
                 gripper: float = 0.80, duration_ms: int = 1000,
                 gripper_pwm: Optional[int] = None, include_gripper: bool = True) -> MotionResult:
        ik = self.kin.inverse_pose(xyz_m, pitch_deg=pitch_deg, roll_rad=roll_rad, gripper=gripper)
        if ik is None:
            return MotionResult(False, None, reason=f"IK failed for xyz={list(xyz_m)} pitch={pitch_deg}")
        servo_pwms = getattr(ik, "servo_pwms", None)
        if servo_pwms is not None:
            values = list(servo_pwms)
            if gripper_pwm is not None:
                values[5] = int(gripper_pwm)
            if include_gripper:
                cmd = self.adapter.send_pwm_command(values, duration_ms)
            else:
                cmd = self.adapter.send_partial_pwm_command(dict(enumerate(values[:5])), duration_ms)
        else:
            if include_gripper:
                cmd = self.adapter.send_joint_command(ik.joints_rad, duration_ms)
            else:
                assignments = {
                    mapping.servo_id: mapping.to_pwm(rad)
                    for rad, mapping in zip(ik.joints_rad[:5], self.adapter.joint_maps[:5])
                }
                cmd = self.adapter.send_partial_pwm_command(assignments, duration_ms)
        self.last_ik = ik
        self.current_joints_rad = list(ik.joints_rad)
        return MotionResult(True, ik, command=cmd)
