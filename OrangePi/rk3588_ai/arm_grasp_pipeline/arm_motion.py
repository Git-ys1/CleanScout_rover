# coding: utf-8
"""High-level arm motion: base xyz -> IK -> RF1 serial text protocol."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

import numpy as np

from .official_kinematics import OfficialIKResult
from .serial_servo_adapter import SerialServoArmAdapter


@dataclass
class MotionResult:
    ok: bool
    ik: Optional[object]
    command: str = ""
    reason: str = ""


class ArmMotion:
    def __init__(
        self,
        adapter: SerialServoArmAdapter,
        kinematics=None,
        reference_tool_matrix: Optional[np.ndarray] = None,
    ) -> None:
        self.adapter = adapter
        if kinematics is None:
            raise ValueError("an explicit kinematics backend is required")
        self.kin = kinematics
        self.last_ik: Optional[object] = None
        self.reference_tool_matrix = (
            None if reference_tool_matrix is None else np.asarray(reference_tool_matrix, dtype=float)
        )

    def current_tool_matrix_from_last_command(self) -> np.ndarray:
        if self.last_ik is not None and getattr(self.last_ik, "tool_matrix", None) is not None:
            return np.asarray(self.last_ik.tool_matrix, dtype=float).copy()
        if self.last_ik is None and self.reference_tool_matrix is not None:
            return self.reference_tool_matrix.copy()
        raise RuntimeError("no calibrated reference/tool matrix is available")

    def pack_ik_command(self, ik, duration_ms: int, gripper_pwm: Optional[int] = None,
                        include_gripper: bool = True) -> str:
        if isinstance(ik, OfficialIKResult):
            if include_gripper or gripper_pwm is not None:
                raise ValueError("official $KMS controls only Servo000..003; command Servo005 separately")
            return self.adapter.pack_kinematics_command(ik.target_xyz_m, duration_ms)
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

    def set_reference_tool_matrix(self, matrix: np.ndarray) -> None:
        self.reference_tool_matrix = np.asarray(matrix, dtype=float).copy()
        self.last_ik = None

    def move_xyz(self, xyz_m: Iterable[float], pitch_deg: float = 70.0, roll_rad: float = -0.05,
                 gripper: float = 0.80, duration_ms: int = 1000,
                 gripper_pwm: Optional[int] = None, include_gripper: bool = True) -> MotionResult:
        ik = self.kin.inverse_pose(xyz_m, pitch_deg=pitch_deg, roll_rad=roll_rad, gripper=gripper)
        if ik is None:
            return MotionResult(False, None, reason=f"IK failed for xyz={list(xyz_m)} pitch={pitch_deg}")
        if isinstance(ik, OfficialIKResult):
            if include_gripper or gripper_pwm is not None:
                return MotionResult(
                    False,
                    ik,
                    reason="official $KMS controls only Servo000..003; command Servo005 separately",
                )
            cmd = self.adapter.send_kinematics_command(ik.target_xyz_m, duration_ms)
        else:
            servo_pwms = getattr(ik, "servo_pwms", None)
            if servo_pwms is not None:
                values = list(servo_pwms)
                if gripper_pwm is not None:
                    values[5] = int(gripper_pwm)
                if include_gripper:
                    cmd = self.adapter.send_pwm_command(values, duration_ms)
                else:
                    cmd = self.adapter.send_partial_pwm_command(dict(enumerate(values[:5])), duration_ms)
            elif include_gripper:
                cmd = self.adapter.send_joint_command(ik.joints_rad, duration_ms)
            else:
                assignments = {
                    mapping.servo_id: mapping.to_pwm(rad)
                    for rad, mapping in zip(ik.joints_rad[:5], self.adapter.joint_maps[:5])
                }
                cmd = self.adapter.send_partial_pwm_command(assignments, duration_ms)
        self.last_ik = ik
        return MotionResult(True, ik, command=cmd)
