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
        kinematics: Optional[Arm5DoFKinematics] = None,
        current_joints_rad: Optional[Sequence[float]] = None,
    ) -> None:
        self.adapter = adapter
        self.kin = kinematics or Arm5DoFKinematics()
        self.last_ik: Optional[IKResult] = None
        self.current_joints_rad = list(current_joints_rad or [0.0, -0.93, 1.6, 1.2, 0.0, 0.801])

    def current_ee_matrix_from_last_command(self) -> np.ndarray:
        if self.last_ik is None:
            return self.kin.forward_matrix(self.current_joints_rad[:5])
        return self.kin.forward_matrix(self.last_ik.joints_rad[:5])

    def move_xyz(self, xyz_m: Iterable[float], pitch_deg: float = 70.0, roll_rad: float = -0.05,
                 gripper: float = 0.80, duration_ms: int = 1000) -> MotionResult:
        ik = self.kin.inverse_pose(xyz_m, pitch_deg=pitch_deg, roll_rad=roll_rad, gripper=gripper)
        if ik is None:
            return MotionResult(False, None, reason=f"IK failed for xyz={list(xyz_m)} pitch={pitch_deg}")
        cmd = self.adapter.send_joint_command(ik.joints_rad, duration_ms)
        self.last_ik = ik
        self.current_joints_rad = list(ik.joints_rad)
        return MotionResult(True, ik, command=cmd)
