# coding: utf-8
"""Kinematics matching the STM32F103 official mechanical-arm firmware.

The source of truth is firmware/mechanical_arm_official_baseline/User/
Components/y_kinematics plus its kinematics_move() wrapper. Public XYZ uses
[forward, left, up] metres; firmware $KMS uses [left, forward, up] millimetres.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Optional, Tuple

import numpy as np


PWM_PER_DEG = 2000.0 / 270.0
PWM_PER_RAD = PWM_PER_DEG * 180.0 / math.pi


@dataclass(frozen=True)
class OfficialIKResult:
    joints_rad: Tuple[float, float, float, float, float, float]
    final_pitch_deg: float
    target_xyz_m: Tuple[float, float, float]
    servo_angles_deg: Tuple[float, float, float, float]
    servo_pwms: Tuple[int, int, int, int, int, int]
    tool_matrix: np.ndarray


class OfficialArmKinematics:
    """Exact Python port of y_kinematics.c with a deterministic forward model."""

    def __init__(self, l0_m: float = 0.100, l1_m: float = 0.105,
                 l2_m: float = 0.088, l3_m: float = 0.155) -> None:
        self.l0_m = float(l0_m)
        self.l1_m = float(l1_m)
        self.l2_m = float(l2_m)
        self.l3_m = float(l3_m)

    @staticmethod
    def _pwm_targets(angles_deg, roll_rad: float, gripper: float):
        a0, a1, a2, a3 = [float(value) for value in angles_deg]
        # Servo003 is reversed once by kinematics_move() in the official firmware.
        pwms = [
            int(1500.0 - PWM_PER_DEG * a0),
            int(1500.0 + PWM_PER_DEG * a1),
            int(1500.0 + PWM_PER_DEG * a2),
            int(1500.0 + PWM_PER_DEG * a3),
            int(round(1500.0 - PWM_PER_RAD * float(roll_rad))),
            int(round(1500.0 - PWM_PER_RAD * float(gripper))),
        ]
        if any(value < 500 or value > 2500 for value in pwms):
            return None
        return tuple(pwms)

    def _solve_alpha(self, xyz_m, alpha_deg: float):
        forward, left, up = [float(value) for value in xyz_m]
        if forward < 0.0:
            return None

        x = left * 1000.0
        y = forward * 1000.0
        z = up * 1000.0
        l0 = self.l0_m * 1000.0
        l1 = self.l1_m * 1000.0
        l2 = self.l2_m * 1000.0
        l3 = self.l3_m * 1000.0

        theta6 = 0.0 if abs(x) < 1e-12 else math.atan(x / y) * 270.0 / math.pi
        radial = math.hypot(x, y)
        alpha = math.radians(float(alpha_deg))
        wrist_y = radial - l3 * math.cos(alpha)
        wrist_z = z - l0 - l3 * math.sin(alpha)
        distance = math.hypot(wrist_y, wrist_z)
        if wrist_z < -l0 or distance <= 1e-9 or distance > l1 + l2:
            return None

        ccc_arg = wrist_y / distance
        bbb = (wrist_y * wrist_y + wrist_z * wrist_z + l1 * l1 - l2 * l2) / (2.0 * l1 * distance)
        aaa = -(wrist_y * wrist_y + wrist_z * wrist_z - l1 * l1 - l2 * l2) / (2.0 * l1 * l2)
        if not (-1.0 <= ccc_arg <= 1.0 and -1.0 <= bbb <= 1.0 and -1.0 <= aaa <= 1.0):
            return None

        z_sign = -1.0 if wrist_z < 0.0 else 1.0
        theta5 = math.degrees(math.acos(ccc_arg) * z_sign + math.acos(bbb))
        theta4 = 180.0 - math.degrees(math.acos(aaa))
        theta3 = float(alpha_deg) - theta5 + theta4
        if theta5 < 0.0 or theta5 > 180.0:
            return None
        if theta4 < -135.0 or theta4 > 135.0:
            return None
        if theta3 < -90.0 or theta3 > 90.0:
            return None
        return (theta6, theta5 - 90.0, theta4, theta3)

    def inverse_pose(self, tool_xyz_m: Iterable[float], pitch_deg: float = 70.0,
                     roll_rad: float = -0.05, gripper: float = 0.80,
                     search_step_deg: int = 1) -> Optional[OfficialIKResult]:
        del pitch_deg  # Official firmware scans Alpha and selects the deepest valid angle.
        xyz = tuple(float(value) for value in tool_xyz_m)
        if len(xyz) != 3 or search_step_deg <= 0:
            raise ValueError("tool_xyz_m must have three values and search_step_deg must be positive")

        chosen = None
        chosen_alpha = None
        for alpha_deg in range(0, -136, -int(search_step_deg)):
            angles = self._solve_alpha(xyz, float(alpha_deg))
            if angles is not None:
                chosen = angles
                chosen_alpha = float(alpha_deg)
        if chosen is None or chosen_alpha is None:
            return None

        pwms = self._pwm_targets(chosen, roll_rad, gripper)
        if pwms is None:
            return None
        phi_rad = math.radians(chosen[0] * 180.0 / 270.0)
        joints = (
            phi_rad,
            math.radians(chosen[1]),
            math.radians(chosen[2]),
            math.radians(chosen[3]),
            float(roll_rad),
            float(gripper),
        )
        return OfficialIKResult(
            joints_rad=joints,
            final_pitch_deg=abs(chosen_alpha),
            target_xyz_m=xyz,
            servo_angles_deg=tuple(float(value) for value in chosen),
            servo_pwms=pwms,
            tool_matrix=self._tool_matrix(xyz, chosen_alpha),
        )

    @staticmethod
    def _tool_matrix(xyz_m, alpha_deg: float, phi_rad: Optional[float] = None) -> np.ndarray:
        forward, left, up = [float(value) for value in xyz_m]
        if phi_rad is None:
            phi_rad = math.atan2(left, forward)
        alpha = math.radians(float(alpha_deg))

        z_axis = np.array([
            math.cos(alpha) * math.cos(phi_rad),
            math.cos(alpha) * math.sin(phi_rad),
            math.sin(alpha),
        ], dtype=float)
        y_axis = np.array([-math.sin(phi_rad), math.cos(phi_rad), 0.0], dtype=float)
        x_axis = np.cross(y_axis, z_axis)
        matrix = np.eye(4, dtype=float)
        matrix[:3, 0] = x_axis
        matrix[:3, 1] = y_axis
        matrix[:3, 2] = z_axis
        matrix[:3, 3] = [forward, left, up]
        return matrix

    def forward_matrix_from_pwm(self, servo_pwms: Iterable[int]) -> np.ndarray:
        values = [int(value) for value in servo_pwms]
        if len(values) < 4:
            raise ValueError("forward_matrix_from_pwm expects at least four PWM values")
        p0, p1, p2, p3 = values[:4]
        angle0 = (1500.0 - p0) / PWM_PER_DEG
        angle1 = (p1 - 1500.0) / PWM_PER_DEG
        angle2 = (p2 - 1500.0) / PWM_PER_DEG
        angle3 = (p3 - 1500.0) / PWM_PER_DEG
        phi = angle0 * math.pi / 270.0
        theta5 = math.radians(angle1 + 90.0)
        theta4 = math.radians(angle2)
        alpha_deg = angle3 + (angle1 + 90.0) - angle2
        alpha = math.radians(alpha_deg)

        radial = (
            self.l1_m * math.cos(theta5)
            + self.l2_m * math.cos(theta5 - theta4)
            + self.l3_m * math.cos(alpha)
        )
        up = (
            self.l0_m
            + self.l1_m * math.sin(theta5)
            + self.l2_m * math.sin(theta5 - theta4)
            + self.l3_m * math.sin(alpha)
        )
        xyz = (radial * math.cos(phi), radial * math.sin(phi), up)
        return self._tool_matrix(xyz, alpha_deg, phi_rad=phi)
