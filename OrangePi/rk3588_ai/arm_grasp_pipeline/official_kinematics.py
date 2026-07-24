# coding: utf-8
"""Measured CleanScout arm kinematics with an explicit Servo004-stator wrist.

The arm body ends at ``wrist`` (the Servo004 stator axis).  Open and closed
gripper centres are separate rigid tool transforms and are never folded into
the body link lengths.  Public XYZ is ``[forward, left, up]`` in metres.

The PWM zero, sign and per-joint slope values are injected from the frozen
C-5.2.5 configuration.  Nothing in this module estimates or changes them.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Mapping, Optional, Sequence, Tuple
import warnings

import numpy as np

from .geometry import invert_transform, validate_rigid_transform


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
    # ``tool_matrix`` is retained for the legacy call sites.  In the new API
    # it is the predicted T_base_tcp after PWM quantisation.
    tool_matrix: np.ndarray
    wrist_matrix: Optional[np.ndarray] = None
    tcp_matrix: Optional[np.ndarray] = None
    tcp_name: str = "closed"


class OfficialArmKinematics:
    """Official planar geometry using the measured CleanScout PWM semantics."""

    def __init__(
        self,
        l0_m: float = 0.100,
        l1_m: float = 0.130,
        l2_m: float = 0.065,
        wrist_link_m: float = 0.055,
        legacy_tool_length_m: float = 0.190,
        raw_pwm_min: int = RAW_PWM_MIN,
        raw_pwm_max: int = RAW_PWM_MAX,
        travel_deg: float = RAW_TRAVEL_DEG,
        zero_pwms: Sequence[int] = DEFAULT_ZERO_PWMS,
        pwm_signs: Sequence[int] = DEFAULT_PWM_SIGNS,
        pwm_per_deg_by_joint: Sequence[float] = DEFAULT_PWM_PER_DEG_BY_JOINT,
        command_pwm_min: int = 500,
        command_pwm_max: int = 2490,
    ) -> None:
        self.l0_m = float(l0_m)
        self.l1_m = float(l1_m)
        self.l2_m = float(l2_m)
        self.wrist_link_m = float(wrist_link_m)
        self.legacy_tool_length_m = float(legacy_tool_length_m)
        # Compatibility only.  Dynamic code must use wrist_link_m plus an
        # explicit T_wrist_tcp matrix.
        self.l3_m = self.legacy_tool_length_m
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

        lengths = (
            self.l0_m,
            self.l1_m,
            self.l2_m,
            self.wrist_link_m,
            self.legacy_tool_length_m,
        )
        if not all(math.isfinite(value) and value > 0.0 for value in lengths):
            raise ValueError("link lengths must be positive and finite")
        if self.legacy_tool_length_m < self.wrist_link_m:
            raise ValueError("legacy tool length cannot end before the wrist")
        if not math.isfinite(self.travel_deg) or self.travel_deg <= 0.0:
            raise ValueError("travel_deg must be positive and finite")
        if self.raw_pwm_min >= self.raw_pwm_max:
            raise ValueError("raw PWM minimum must be lower than maximum")
        if (
            len(self.zero_pwms) != 4
            or len(self.pwm_signs) != 4
            or len(self.pwm_per_deg_by_joint) != 4
        ):
            raise ValueError(
                "zero_pwms, pwm_signs and pwm_per_deg_by_joint must contain Servo000..003"
            )
        if any(sign not in (-1, 1) for sign in self.pwm_signs):
            raise ValueError("each PWM sign must be +1 or -1")
        if any(
            not math.isfinite(value) or value <= 0.0
            for value in self.pwm_per_deg_by_joint
        ):
            raise ValueError("each per-joint PWM/degree value must be positive")
        if (
            self.command_pwm_min < self.raw_pwm_min
            or self.command_pwm_max > self.raw_pwm_max
            or self.command_pwm_min >= self.command_pwm_max
        ):
            raise ValueError("controller PWM range must stay inside the raw range")
        if any(
            value < self.raw_pwm_min or value > self.raw_pwm_max
            for value in self.zero_pwms
        ):
            raise ValueError("joint zero PWM is outside the raw servo range")
        self.pwm_per_deg = float(self.raw_pwm_max - self.raw_pwm_min) / self.travel_deg

    @classmethod
    def from_config(cls, kinematics: Mapping, joint_calibration: Mapping):
        required_kinematics = {"l0_m", "l1_m", "l2_m", "wrist_link_m"}
        missing = sorted(required_kinematics.difference(kinematics))
        if missing:
            # A clear failure is preferable to silently treating the old l3_m
            # as both an arm link and a TCP.
            raise ValueError(
                "kinematics config missing dynamic fields: " + ", ".join(missing)
            )
        required_joint = {
            "raw_pwm_min",
            "raw_pwm_max",
            "travel_deg",
            "zero_pwms",
            "pwm_signs",
            "pwm_per_deg_by_joint",
            "command_pwm_min",
            "command_pwm_max",
        }
        missing = sorted(required_joint.difference(joint_calibration))
        if missing:
            raise ValueError(
                "joint_pwm_calibration missing fields: " + ", ".join(missing)
            )
        legacy_length = kinematics.get(
            "measured_l3_total_closed_m",
            kinematics.get("legacy_tool_length_m", kinematics.get("l3_m", 0.190)),
        )
        return cls(
            l0_m=float(kinematics["l0_m"]),
            l1_m=float(kinematics["l1_m"]),
            l2_m=float(kinematics["l2_m"]),
            wrist_link_m=float(kinematics["wrist_link_m"]),
            legacy_tool_length_m=float(legacy_length),
            raw_pwm_min=int(joint_calibration["raw_pwm_min"]),
            raw_pwm_max=int(joint_calibration["raw_pwm_max"]),
            travel_deg=float(joint_calibration["travel_deg"]),
            zero_pwms=joint_calibration["zero_pwms"],
            pwm_signs=joint_calibration["pwm_signs"],
            pwm_per_deg_by_joint=joint_calibration["pwm_per_deg_by_joint"],
            command_pwm_min=int(joint_calibration["command_pwm_min"]),
            command_pwm_max=int(joint_calibration["command_pwm_max"]),
        )

    def joint_angles_deg_to_pwm(
        self, joint_angles_deg: Iterable[float]
    ) -> Optional[Tuple[int, int, int, int]]:
        angles = tuple(float(value) for value in joint_angles_deg)
        if len(angles) != 4 or not all(math.isfinite(value) for value in angles):
            raise ValueError("joint_angles_deg must contain four finite values")
        pwms = tuple(
            int(round(zero + sign * slope * angle))
            for zero, sign, slope, angle in zip(
                self.zero_pwms,
                self.pwm_signs,
                self.pwm_per_deg_by_joint,
                angles,
            )
        )
        if any(
            value < self.command_pwm_min or value > self.command_pwm_max
            for value in pwms
        ):
            return None
        return pwms

    # Historical private name retained for old planner/tests.
    def _pwm_targets(self, angles_deg):
        return self.joint_angles_deg_to_pwm(angles_deg)

    def pwm_to_joint_angles_deg(
        self, servo_pwms_000_003: Iterable[int]
    ) -> Tuple[float, float, float, float]:
        values = tuple(int(value) for value in servo_pwms_000_003)
        if len(values) != 4:
            raise ValueError("exactly Servo000..003 PWM values are required")
        if any(
            value < self.command_pwm_min or value > self.command_pwm_max
            for value in values
        ):
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

    # Historical private name retained for old tests.
    def _angles_from_pwm(self, servo_pwms):
        values = tuple(int(value) for value in servo_pwms)
        if len(values) < 4:
            raise ValueError("Servo000..003 PWM values are required")
        return self.pwm_to_joint_angles_deg(values[:4])

    @staticmethod
    def _endpoint_matrix(
        xyz_m: Iterable[float], alpha_deg: float, phi_rad: Optional[float] = None
    ) -> np.ndarray:
        forward, left, up = [float(value) for value in xyz_m]
        if phi_rad is None:
            phi_rad = math.atan2(left, forward)
        alpha = math.radians(float(alpha_deg))
        x_axis = np.array(
            [
                math.cos(alpha) * math.cos(phi_rad),
                math.cos(alpha) * math.sin(phi_rad),
                math.sin(alpha),
            ],
            dtype=float,
        )
        y_axis = np.array(
            [-math.sin(phi_rad), math.cos(phi_rad), 0.0], dtype=float
        )
        z_axis = np.cross(x_axis, y_axis)
        matrix = np.eye(4, dtype=float)
        matrix[:3, 0] = x_axis
        matrix[:3, 1] = y_axis
        matrix[:3, 2] = z_axis
        matrix[:3, 3] = (forward, left, up)
        return validate_rigid_transform(matrix, "T_base_endpoint")

    # Historical name retained for legacy code.
    _tool_matrix = _endpoint_matrix

    def forward_wrist_matrix_from_angles(
        self, joint_angles_deg: Iterable[float]
    ) -> np.ndarray:
        """Return ``T_base_wrist`` at the Servo004 stator axis."""

        q0, q1, q2, q3 = tuple(float(value) for value in joint_angles_deg)
        if not all(math.isfinite(value) for value in (q0, q1, q2, q3)):
            raise ValueError("joint_angles_deg must contain four finite values")
        phi = math.radians(q0)
        theta5 = math.radians(90.0 - q1)
        theta4 = math.radians(q2)
        alpha_deg = q3 + 90.0 - q1 - q2
        alpha = math.radians(alpha_deg)
        radial = (
            self.l1_m * math.cos(theta5)
            + self.l2_m * math.cos(theta5 - theta4)
            + self.wrist_link_m * math.cos(alpha)
        )
        up = (
            self.l0_m
            + self.l1_m * math.sin(theta5)
            + self.l2_m * math.sin(theta5 - theta4)
            + self.wrist_link_m * math.sin(alpha)
        )
        xyz = (radial * math.cos(phi), radial * math.sin(phi), up)
        return self._endpoint_matrix(xyz, alpha_deg, phi_rad=phi)

    def forward_wrist_matrix_from_pwm(
        self, servo_pwms_000_003: Iterable[int]
    ) -> np.ndarray:
        return self.forward_wrist_matrix_from_angles(
            self.pwm_to_joint_angles_deg(servo_pwms_000_003)
        )

    def forward_tcp_matrix_from_pwm(
        self,
        servo_pwms_000_003: Iterable[int],
        T_wrist_tcp: np.ndarray,
    ) -> np.ndarray:
        wrist_tcp = validate_rigid_transform(T_wrist_tcp, "T_wrist_tcp")
        return validate_rigid_transform(
            self.forward_wrist_matrix_from_pwm(servo_pwms_000_003) @ wrist_tcp,
            "T_base_tcp",
        )

    def _solve_endpoint(
        self,
        endpoint_xyz_m: Iterable[float],
        alpha_deg: float,
        end_link_m: float,
        phi_rad: Optional[float] = None,
    ) -> Optional[Tuple[float, float, float, float]]:
        forward, left, up = [float(value) for value in endpoint_xyz_m]
        if not all(math.isfinite(value) for value in (forward, left, up, alpha_deg)):
            raise ValueError("endpoint pose values must be finite")
        x = left * 1000.0
        y = forward * 1000.0
        z = up * 1000.0
        l0 = self.l0_m * 1000.0
        l1 = self.l1_m * 1000.0
        l2 = self.l2_m * 1000.0
        l3 = float(end_link_m) * 1000.0
        if phi_rad is None:
            phi_rad = math.atan2(x, y)
        q0 = math.degrees(float(phi_rad))
        # A folded arm can place the wrist behind the base axis while its TCP
        # and +X tool axis still point forward.  Keep the signed radial
        # projection instead of using hypot(endpoint) to infer q0.
        radial = y * math.cos(phi_rad) + x * math.sin(phi_rad)
        lateral_residual = -y * math.sin(phi_rad) + x * math.cos(phi_rad)
        if abs(lateral_residual) > 1e-3:
            return None
        alpha = math.radians(float(alpha_deg))
        joint3_y = radial - l3 * math.cos(alpha)
        joint3_z = z - l0 - l3 * math.sin(alpha)
        distance = math.hypot(joint3_y, joint3_z)
        tolerance = 1e-6
        if (
            distance <= 1e-9
            or distance > l1 + l2 + tolerance
            or distance < abs(l1 - l2) - tolerance
        ):
            return None

        ccc_arg = joint3_y / distance
        bbb = (
            joint3_y * joint3_y
            + joint3_z * joint3_z
            + l1 * l1
            - l2 * l2
        ) / (2.0 * l1 * distance)
        aaa = -(
            joint3_y * joint3_y
            + joint3_z * joint3_z
            - l1 * l1
            - l2 * l2
        ) / (2.0 * l1 * l2)
        if not all(-1.0 - 1e-9 <= value <= 1.0 + 1e-9 for value in (
            ccc_arg, bbb, aaa
        )):
            return None
        ccc_arg = float(np.clip(ccc_arg, -1.0, 1.0))
        bbb = float(np.clip(bbb, -1.0, 1.0))
        aaa = float(np.clip(aaa, -1.0, 1.0))

        z_sign = -1.0 if joint3_z < 0.0 else 1.0
        theta5 = math.degrees(
            math.acos(ccc_arg) * z_sign + math.acos(bbb)
        )
        theta4 = 180.0 - math.degrees(math.acos(aaa))
        q1 = 90.0 - theta5
        q2 = theta4
        q3 = float(alpha_deg) - theta5 + theta4
        angles = (q0, q1, q2, q3)
        # PWM conversion is the authoritative joint-range gate.
        if self.joint_angles_deg_to_pwm(angles) is None:
            return None
        return angles

    def inverse_tcp_pose(
        self,
        target_T_base_tcp: Optional[np.ndarray] = None,
        target_xyz_m: Optional[Iterable[float]] = None,
        pitch_deg: Optional[float] = None,
        T_wrist_tcp: Optional[np.ndarray] = None,
        tcp_name: str = "closed",
    ) -> Optional[OfficialIKResult]:
        """Solve Servo000..003 so the selected TCP reaches the target pose.

        ``pitch_deg`` is positive downward from horizontal.  With an XYZ-only
        target it is mandatory; with a complete target matrix it is inferred
        from the requested wrist X axis.
        """

        if T_wrist_tcp is None:
            raise ValueError("inverse_tcp_pose requires an explicit T_wrist_tcp")
        wrist_tcp = validate_rigid_transform(T_wrist_tcp, "T_wrist_tcp")
        if (target_T_base_tcp is None) == (target_xyz_m is None):
            raise ValueError(
                "provide exactly one of target_T_base_tcp or target_xyz_m"
            )
        if target_T_base_tcp is None:
            if pitch_deg is None or not math.isfinite(float(pitch_deg)):
                raise ValueError("XYZ-only TCP IK requires a finite pitch_deg")
            requested_pitch = float(pitch_deg)
            if requested_pitch < -135.0 or requested_pitch > 135.0:
                raise ValueError("pitch_deg must be in -135..135")
            xyz = tuple(float(value) for value in target_xyz_m)
            if len(xyz) != 3 or not all(math.isfinite(value) for value in xyz):
                raise ValueError("target_xyz_m must contain three finite values")
            target_tcp = self._endpoint_matrix(xyz, -requested_pitch)
        else:
            target_tcp = validate_rigid_transform(
                target_T_base_tcp, "target_T_base_tcp"
            )
            xyz = tuple(float(value) for value in target_tcp[:3, 3])

        target_wrist = validate_rigid_transform(
            target_tcp @ invert_transform(wrist_tcp), "target_T_base_wrist"
        )
        wrist_x = target_wrist[:3, 0]
        phi_rad = math.atan2(float(wrist_x[1]), float(wrist_x[0]))
        alpha_deg = math.degrees(
            math.atan2(float(wrist_x[2]), float(math.hypot(wrist_x[0], wrist_x[1])))
        )
        angles = self._solve_endpoint(
            target_wrist[:3, 3], alpha_deg, self.wrist_link_m, phi_rad=phi_rad
        )
        if angles is None:
            return None
        pwms = self.joint_angles_deg_to_pwm(angles)
        if pwms is None:
            return None
        predicted_wrist = self.forward_wrist_matrix_from_pwm(pwms)
        predicted_tcp = validate_rigid_transform(
            predicted_wrist @ wrist_tcp, "predicted_T_base_tcp"
        )
        final_pitch = -math.degrees(
            math.atan2(
                float(predicted_tcp[2, 0]),
                float(math.hypot(predicted_tcp[0, 0], predicted_tcp[1, 0])),
            )
        )
        frozen_wrist = predicted_wrist.copy()
        frozen_tcp = predicted_tcp.copy()
        frozen_wrist.setflags(write=False)
        frozen_tcp.setflags(write=False)
        return OfficialIKResult(
            joints_rad=tuple(math.radians(value) for value in angles),
            final_pitch_deg=float(final_pitch),
            target_xyz_m=xyz,
            servo_angles_deg=tuple(float(value) for value in angles),
            servo_pwms=tuple(int(value) for value in pwms),
            tool_matrix=frozen_tcp,
            wrist_matrix=frozen_wrist,
            tcp_matrix=frozen_tcp,
            tcp_name=str(tcp_name),
        )

    def inverse_pose(
        self,
        tool_xyz_m: Iterable[float],
        pitch_deg: Optional[float] = None,
        roll_rad: float = -0.05,
        gripper: float = 0.80,
        search_step_deg: int = 1,
    ) -> Optional[OfficialIKResult]:
        """Deprecated legacy IK using the measured total closed length."""

        del roll_rad, gripper
        warnings.warn(
            "inverse_pose is legacy; dynamic grasp must call inverse_tcp_pose",
            DeprecationWarning,
            stacklevel=2,
        )
        xyz = tuple(float(value) for value in tool_xyz_m)
        if len(xyz) != 3 or search_step_deg <= 0:
            raise ValueError("tool_xyz_m must have three values")
        tool_offset = self.legacy_tool_length_m - self.wrist_link_m
        T_wrist_tcp = np.eye(4, dtype=float)
        T_wrist_tcp[0, 3] = tool_offset
        if pitch_deg is not None:
            return self.inverse_tcp_pose(
                target_xyz_m=xyz,
                pitch_deg=float(pitch_deg),
                T_wrist_tcp=T_wrist_tcp,
                tcp_name="legacy",
            )
        # Preserve the vendor diagnostic pitch scan without carrying it into
        # the new runtime.
        chosen = None
        for alpha_deg in range(0, -136, -int(search_step_deg)):
            candidate = self.inverse_tcp_pose(
                target_xyz_m=xyz,
                pitch_deg=-float(alpha_deg),
                T_wrist_tcp=T_wrist_tcp,
                tcp_name="legacy",
            )
            if candidate is not None:
                chosen = candidate
        return chosen

    def estimate_tool_matrix_from_pwm(self, servo_pwms: Iterable[int]) -> np.ndarray:
        """Deprecated legacy total-length FK; never use for dynamic hand-eye."""

        warnings.warn(
            "estimate_tool_matrix_from_pwm is legacy; use forward_wrist_matrix_from_pwm",
            DeprecationWarning,
            stacklevel=2,
        )
        offset = np.eye(4, dtype=float)
        offset[0, 3] = self.legacy_tool_length_m - self.wrist_link_m
        values = tuple(int(value) for value in servo_pwms)
        return self.forward_tcp_matrix_from_pwm(values[:4], offset)
