# coding: utf-8
"""Kinematics for the measured CleanScout six-servo arm.

The geometric solver follows the official STM32F103 example, but angle-to-PWM
conversion follows the C-5.2.5 measurements instead of the vendor defaults.
Public XYZ is ``[forward, left, up]`` in metres. Servo004 remains fixed and
Servo005 is controlled by the grasp stages, so IK owns Servo000..003 only.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Mapping, Optional, Sequence, Tuple

import numpy as np


RAW_PWM_MIN = 500
RAW_PWM_MAX = 2700
RAW_TRAVEL_DEG = 270.0
PWM_PER_DEG = (RAW_PWM_MAX - RAW_PWM_MIN) / RAW_TRAVEL_DEG
DEFAULT_ZERO_PWMS = (1500, 1500, 1500, 1500)
DEFAULT_PWM_PER_DEG_BY_JOINT = (PWM_PER_DEG,) * 4
# Positive semantic angle: left yaw, L1 forward, elbow fold, tip raise.
DEFAULT_PWM_SIGNS = (1, -1, 1, 1)


@dataclass(frozen=True)
class OfficialIKResult:
    joints_rad: Tuple[float, float, float, float]
    final_pitch_deg: float
    target_xyz_m: Tuple[float, float, float]
    servo_angles_deg: Tuple[float, float, float, float]
    servo_pwms: Tuple[int, int, int, int]
    tool_matrix: np.ndarray


class OfficialArmKinematics:
    """Official planar geometry with measured C-5.2.5 joint semantics."""

    def __init__(self, l0_m: float = 0.100, l1_m: float = 0.105,
                 l2_m: float = 0.088, l3_m: float = 0.155,
                 raw_pwm_min: int = RAW_PWM_MIN,
                 raw_pwm_max: int = RAW_PWM_MAX,
                 travel_deg: float = RAW_TRAVEL_DEG,
                 zero_pwms: Sequence[int] = DEFAULT_ZERO_PWMS,
                 pwm_signs: Sequence[int] = DEFAULT_PWM_SIGNS,
                 pwm_per_deg_by_joint: Sequence[float] = DEFAULT_PWM_PER_DEG_BY_JOINT,
                 command_pwm_min: int = 500,
                 command_pwm_max: int = 2490) -> None:
        self.l0_m = float(l0_m)
        self.l1_m = float(l1_m)
        self.l2_m = float(l2_m)
        self.l3_m = float(l3_m)
        self.raw_pwm_min = int(raw_pwm_min)
        self.raw_pwm_max = int(raw_pwm_max)
        self.travel_deg = float(travel_deg)
        self.zero_pwms = tuple(int(value) for value in zero_pwms)
        self.pwm_signs = tuple(int(value) for value in pwm_signs)
        self.pwm_per_deg_by_joint = tuple(
            float(value) for value in pwm_per_deg_by_joint
        )
        self.command_pwm_min = int(command_pwm_min)
        self.command_pwm_max = int(command_pwm_max)
        if not all(math.isfinite(value) and value > 0.0 for value in (
                self.l0_m, self.l1_m, self.l2_m, self.l3_m, self.travel_deg)):
            raise ValueError("link lengths and travel_deg must be positive and finite")
        if self.raw_pwm_min >= self.raw_pwm_max:
            raise ValueError("raw PWM minimum must be lower than maximum")
        if (len(self.zero_pwms) != 4 or len(self.pwm_signs) != 4
                or len(self.pwm_per_deg_by_joint) != 4):
            raise ValueError(
                "zero_pwms, pwm_signs, and pwm_per_deg_by_joint must contain Servo000..003"
            )
        if any(sign not in (-1, 1) for sign in self.pwm_signs):
            raise ValueError("each PWM sign must be +1 or -1")
        if any(not math.isfinite(value) or value <= 0.0
               for value in self.pwm_per_deg_by_joint):
            raise ValueError("each per-joint PWM/degree value must be positive and finite")
        if self.command_pwm_min < self.raw_pwm_min or self.command_pwm_max > self.raw_pwm_max:
            raise ValueError("controller PWM range must stay inside vendor raw range")
        if self.command_pwm_min >= self.command_pwm_max:
            raise ValueError("controller PWM minimum must be lower than maximum")
        if any(value < self.raw_pwm_min or value > self.raw_pwm_max
               for value in self.zero_pwms):
            raise ValueError("joint zero PWM is outside the raw servo range")
        # Kept for nominal vendor documentation/backward compatibility only.
        # Motion conversion uses pwm_per_deg_by_joint exclusively.
        self.pwm_per_deg = (
            float(self.raw_pwm_max - self.raw_pwm_min) / self.travel_deg
        )

    @classmethod
    def from_config(cls, kinematics: Mapping, joint_calibration: Mapping):
        required_kinematics = {"l0_m", "l1_m", "l2_m", "l3_m"}
        missing = sorted(required_kinematics.difference(kinematics))
        if missing:
            raise ValueError("kinematics config missing fields: " + ", ".join(missing))
        required_joint = {
            "raw_pwm_min", "raw_pwm_max", "travel_deg", "zero_pwms", "pwm_signs",
            "pwm_per_deg_by_joint", "command_pwm_min", "command_pwm_max",
        }
        missing = sorted(required_joint.difference(joint_calibration))
        if missing:
            raise ValueError("joint_pwm_calibration missing fields: " + ", ".join(missing))
        return cls(
            l0_m=float(kinematics["l0_m"]),
            l1_m=float(kinematics["l1_m"]),
            l2_m=float(kinematics["l2_m"]),
            l3_m=float(kinematics["l3_m"]),
            raw_pwm_min=int(joint_calibration["raw_pwm_min"]),
            raw_pwm_max=int(joint_calibration["raw_pwm_max"]),
            travel_deg=float(joint_calibration["travel_deg"]),
            zero_pwms=joint_calibration["zero_pwms"],
            pwm_signs=joint_calibration["pwm_signs"],
            pwm_per_deg_by_joint=joint_calibration["pwm_per_deg_by_joint"],
            command_pwm_min=int(joint_calibration["command_pwm_min"]),
            command_pwm_max=int(joint_calibration["command_pwm_max"]),
        )

    def _pwm_targets(self, angles_deg):
        angles = tuple(float(value) for value in angles_deg)
        if len(angles) != 4 or not all(math.isfinite(value) for value in angles):
            raise ValueError("angles_deg must contain four finite values")
        pwms = tuple(int(round(zero + sign * slope * angle))
                     for zero, sign, slope, angle in zip(
                         self.zero_pwms,
                         self.pwm_signs,
                         self.pwm_per_deg_by_joint,
                         angles,
                     ))
        if any(value < self.command_pwm_min or value > self.command_pwm_max
               for value in pwms):
            return None
        return pwms

    def _angles_from_pwm(self, servo_pwms):
        values = tuple(int(value) for value in servo_pwms)
        if len(values) < 4:
            raise ValueError("Servo000..003 PWM values are required")
        values = values[:4]
        if any(value < self.command_pwm_min or value > self.command_pwm_max
               for value in values):
            raise ValueError("servo PWM is outside the controller command range")
        return tuple(
            (value - zero) / (sign * slope)
            for value, zero, sign, slope in zip(
                values,
                self.zero_pwms,
                self.pwm_signs,
                self.pwm_per_deg_by_joint,
            )
        )

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

        # q0 is the physical base yaw: forward=0 deg and left/CCW is positive.
        q0 = math.degrees(math.atan2(x, y))
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
        q1 = 90.0 - theta5
        q2 = theta4
        q3 = float(alpha_deg) - theta5 + theta4
        if theta5 < 0.0 or theta5 > 180.0:
            return None
        if q2 < -135.0 or q2 > 135.0:
            return None
        if q3 < -90.0 or q3 > 90.0:
            return None
        return (q0, q1, q2, q3)

    def inverse_pose(self, tool_xyz_m: Iterable[float], pitch_deg: Optional[float] = None,
                     roll_rad: float = -0.05, gripper: float = 0.80,
                     search_step_deg: int = 1) -> Optional[OfficialIKResult]:
        # Positive pitch means downward from horizontal. When omitted, preserve
        # the vendor alpha scan for diagnostics.
        del roll_rad, gripper
        xyz = tuple(float(value) for value in tool_xyz_m)
        if len(xyz) != 3 or search_step_deg <= 0:
            raise ValueError("tool_xyz_m must have three values and search_step_deg must be positive")

        if pitch_deg is None:
            chosen = None
            chosen_alpha = None
            for alpha_deg in range(0, -136, -int(search_step_deg)):
                angles = self._solve_alpha(xyz, float(alpha_deg))
                if angles is not None:
                    chosen = angles
                    chosen_alpha = float(alpha_deg)
        else:
            requested_pitch = float(pitch_deg)
            if not math.isfinite(requested_pitch) or requested_pitch < -90.0 or requested_pitch > 135.0:
                raise ValueError("pitch_deg must be finite and in -90..135")
            chosen_alpha = -requested_pitch
            chosen = self._solve_alpha(xyz, chosen_alpha)
        if chosen is None or chosen_alpha is None:
            return None

        pwms = self._pwm_targets(chosen)
        if pwms is None:
            return None
        joints = tuple(math.radians(value) for value in chosen)
        return OfficialIKResult(
            joints_rad=joints,
            final_pitch_deg=-chosen_alpha,
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

        x_axis = np.array([
            math.cos(alpha) * math.cos(phi_rad),
            math.cos(alpha) * math.sin(phi_rad),
            math.sin(alpha),
        ], dtype=float)
        y_axis = np.array([-math.sin(phi_rad), math.cos(phi_rad), 0.0], dtype=float)
        z_axis = np.cross(x_axis, y_axis)
        matrix = np.eye(4, dtype=float)
        matrix[:3, 0] = x_axis
        matrix[:3, 1] = y_axis
        matrix[:3, 2] = z_axis
        matrix[:3, 3] = [forward, left, up]
        return matrix

    def estimate_tool_matrix_from_pwm(self, servo_pwms: Iterable[int]) -> np.ndarray:
        """Estimate base-to-tool pose for diagnostics, not dynamic hand-eye use."""
        q0, q1, q2, q3 = self._angles_from_pwm(servo_pwms)
        phi = math.radians(q0)
        theta5 = math.radians(90.0 - q1)
        theta4 = math.radians(q2)
        alpha_deg = q3 + 90.0 - q1 - q2
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
