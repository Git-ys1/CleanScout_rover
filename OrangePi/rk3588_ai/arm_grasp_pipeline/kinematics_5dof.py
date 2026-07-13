# coding: utf-8
"""Legacy 5/6DoF model retained for ROS2 source comparison only.

Production grasp execution uses ``official_kinematics.py`` and never selects
this module implicitly.

Important differences from the learning package:
- No global DH mutation in forward kinematics.
- IK input remains metres in the base frame, matching arm_ik_sdk.move_arm().
- The solver preserves the original y-axis sign convention: y is negated before IK.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np

ARM_LINK2 = 1220.0      # 0.1220 m * 10000
ARM_LINK3 = 1220.5      # 0.12205 m * 10000
ARM_LINK4 = 1550.0      # 0.1550 m * 10000
JOINT_LIMIT = (-2.335, 2.335)  # radians, from learning package stero_limit

_BASE_DH = {
    "alpha": [0, -90, 0, 0, 90, 0],
    "a": [0, 0, 0.122, 0.12205, 0, 0],
    "d": [0.0475, 0.0559, 0, 0, 0, 0.0685],
    "theta": [0, 0, -90, 0, 90, 0],
}


@dataclass(frozen=True)
class IKResult:
    joints_rad: List[float]  # [base, shoulder, elbow, wrist_pitch, wrist_roll, gripper]
    final_pitch_deg: float
    target_xyz_m: Tuple[float, float, float]


class Arm5DoFKinematics:
    def __init__(self, base_z_offset_m: float = 0.1034) -> None:
        # arm_ik_sdk.py subtracts 0.1034 before calling IK; keep it explicit here.
        self.base_z_offset_m = float(base_z_offset_m)

    @staticmethod
    def _dh_matrix(a: float, alpha_deg: float, d: float, theta_deg: float) -> np.ndarray:
        alpha = math.radians(alpha_deg)
        theta = math.radians(theta_deg)
        return np.array([
            [math.cos(theta), -math.sin(theta) * math.cos(alpha), math.sin(theta) * math.sin(alpha), a * math.cos(theta)],
            [math.sin(theta), math.cos(theta) * math.cos(alpha), -math.cos(theta) * math.sin(alpha), a * math.sin(theta)],
            [0.0, math.sin(alpha), math.cos(alpha), d],
            [0.0, 0.0, 0.0, 1.0],
        ], dtype=float)

    def forward_matrix(self, joints_rad: Iterable[float]) -> np.ndarray:
        """Forward kinematics matrix, avoiding the global-state bug in the source package."""
        js = list(joints_rad)
        if len(js) < 5:
            raise ValueError("forward_matrix expects at least 5 joint radians")

        theta = list(_BASE_DH["theta"])
        theta[1] = theta[1] - math.degrees(js[0])
        theta[2] = theta[2] + math.degrees(js[1])
        theta[3] = theta[3] + math.degrees(js[2])
        theta[4] = theta[4] + math.degrees(js[3])
        theta[5] = theta[5] + math.degrees(js[4])

        T = np.eye(4)
        for i in range(6):
            T = T @ self._dh_matrix(_BASE_DH["a"][i], _BASE_DH["alpha"][i], _BASE_DH["d"][i], theta[i])
        return T

    @staticmethod
    def _inverse_once(tool_scaled: List[float], pitch_deg: float) -> Optional[Dict[str, float]]:
        theta1 = 0.0
        theta2 = 0.0
        theta3 = 0.0
        theta4 = 0.0

        if not (tool_scaled[0] == 0 and tool_scaled[1] == 0):
            theta1 = math.atan2(tool_scaled[1], tool_scaled[0])
            if theta1 < JOINT_LIMIT[0] or theta1 > JOINT_LIMIT[1]:
                return None

        pitch_rad = math.radians(pitch_deg)
        wrist_x = tool_scaled[0] - ARM_LINK4 * math.cos(pitch_rad) * math.cos(theta1)
        wrist_y = tool_scaled[1] - ARM_LINK4 * math.cos(pitch_rad) * math.sin(theta1)
        wrist_z = tool_scaled[2] + ARM_LINK4 * math.sin(pitch_rad)

        if abs(math.cos(theta1)) > 1e-9:
            b = wrist_x / math.cos(theta1)
        else:
            b = wrist_y / math.sin(theta1)

        cos_theta3 = (wrist_z**2 + b**2 - ARM_LINK2**2 - ARM_LINK3**2) / (2 * ARM_LINK2 * ARM_LINK3)
        if cos_theta3 < -1.0 or cos_theta3 > 1.0:
            return None

        theta3 = math.atan2(math.sqrt(max(0.0, 1.0 - cos_theta3**2)), cos_theta3)
        if theta3 < JOINT_LIMIT[0] or theta3 > JOINT_LIMIT[1]:
            return None

        k1 = ARM_LINK2 + ARM_LINK3 * math.cos(theta3)
        k2 = ARM_LINK3 * math.sin(theta3)
        r = math.sqrt(k1**2 + k2**2)
        theta2 = math.atan2(-wrist_z / r, b / r) - math.atan2(k2 / r, k1 / r)
        if theta2 < JOINT_LIMIT[0] or theta2 > JOINT_LIMIT[1]:
            return None

        theta4 = pitch_rad - (theta2 + theta3)
        if theta4 < JOINT_LIMIT[0] or theta4 > JOINT_LIMIT[1]:
            return None

        theta2 += 1.570795
        return {"theta1": theta1, "theta2": theta2, "theta3": theta3, "theta4": theta4}

    def inverse_pose(
        self,
        tool_xyz_m: Iterable[float],
        pitch_deg: float = 70.0,
        roll_rad: float = -0.05,
        gripper: float = 0.80,
        search_step_deg: int = 1,
    ) -> Optional[IKResult]:
        """Solve IK for an end-effector target in metres.

        tool_xyz_m is the final TCP/gripper target in the arm base frame. This method
        subtracts the source package's 0.1034 m base offset internally.
        """
        xyz = [float(v) for v in tool_xyz_m]
        if len(xyz) != 3:
            raise ValueError("tool_xyz_m must be [x, y, z]")
        if pitch_deg < -90 or pitch_deg > 90:
            raise ValueError("pitch_deg must be in [-90, 90]")

        xyz_for_ik = [xyz[0], xyz[1], xyz[2] - self.base_z_offset_m]
        scaled = [xyz_for_ik[0] * 10000.0, -xyz_for_ik[1] * 10000.0, xyz_for_ik[2] * 10000.0]

        if math.sqrt(sum(v * v for v in scaled)) > (ARM_LINK2 + ARM_LINK3 + ARM_LINK4 + 1e-6):
            return None

        pitch_i = int(pitch_deg)
        up = None
        down = None
        up_pitch = None
        down_pitch = None

        for p in range(pitch_i + search_step_deg, 90, search_step_deg):
            ans = self._inverse_once(scaled, p)
            if ans is not None:
                up, up_pitch = ans, p
                break
        for p in range(pitch_i, -90, -search_step_deg):
            ans = self._inverse_once(scaled, p)
            if ans is not None:
                down, down_pitch = ans, p
                break

        if up is None and down is None:
            return None
        if up is not None and down is not None:
            use_up = abs(up_pitch - pitch_deg) < abs(down_pitch - pitch_deg)
            ans, final_pitch = (up, up_pitch) if use_up else (down, down_pitch)
        elif up is not None:
            ans, final_pitch = up, up_pitch
        else:
            ans, final_pitch = down, down_pitch

        joints = [ans["theta1"], ans["theta2"], ans["theta3"], ans["theta4"], float(roll_rad), float(gripper)]
        return IKResult(joints_rad=joints, final_pitch_deg=float(final_pitch), target_xyz_m=tuple(xyz))
