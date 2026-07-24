# coding: utf-8
"""High-level motion with mandatory PRAD confirmation.

This module deliberately separates these three facts:

* a command could be packed;
* its bytes were written to the serial port;
* every commanded joint was observed at the target by PRAD.

Only the last fact is accepted as physical completion.  Dry-run follows the
same control path but marks every snapshot and result as simulated.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Iterable, Mapping, Optional, Sequence, Tuple
import warnings

import numpy as np

from .geometry import validate_rigid_transform
from .official_kinematics import OfficialIKResult
from .serial_servo_adapter import (
    PWMReadbackError,
    PWMReadbackSnapshot,
    SerialServoArmAdapter,
    ServoCommandResult,
)


DEFAULT_SERVO_PWM_LIMITS: Tuple[Tuple[int, int], ...] = (
    (767, 2233),
    (767, 2233),
    (1500, 2490),
    (500, 2233),
    (1500, 1500),
    (1000, 2200),
)


class MotionSafetyError(RuntimeError):
    """Raised when measured arm state violates a non-negotiable gate."""


@dataclass(frozen=True)
class ActualArmPose:
    matrix: np.ndarray
    snapshot: PWMReadbackSnapshot
    frame: str
    tcp_name: Optional[str] = None

    def __post_init__(self) -> None:
        frozen = validate_rigid_transform(self.matrix, self.frame).copy()
        frozen.setflags(write=False)
        object.__setattr__(self, "matrix", frozen)


@dataclass(frozen=True)
class MotionResult:
    ok: bool
    ik: Optional[object]
    command: str = ""
    reason: str = ""
    command_packed: bool = False
    command_written: bool = False
    readback_reached: bool = False
    simulated: bool = False
    motion_end_monotonic: float = 0.0
    readback_snapshot: Optional[PWMReadbackSnapshot] = None
    readback_mismatches: Mapping[int, Mapping[str, int]] = field(
        default_factory=dict
    )

    @classmethod
    def from_servo_result(cls, result: ServoCommandResult, ik=None):
        return cls(
            ok=bool(result.ok),
            ik=ik,
            command=result.command,
            reason=result.reason,
            command_packed=result.command_packed,
            command_written=result.command_written,
            readback_reached=result.readback_reached,
            simulated=result.simulated,
            motion_end_monotonic=result.motion_end_monotonic,
            readback_snapshot=result.snapshot,
            readback_mismatches=dict(result.mismatches),
        )


class ArmMotion:
    """Execute bounded servo moves and derive poses from measured PWM only."""

    def __init__(
        self,
        adapter: SerialServoArmAdapter,
        kinematics=None,
        reference_tool_matrix: Optional[np.ndarray] = None,
        wrist_fixed_pwm: int = 1500,
        required_readback_ids: Sequence[int] = (0, 1, 2, 3, 4, 5),
        servo_pwm_limits: Sequence[Sequence[int]] = DEFAULT_SERVO_PWM_LIMITS,
        wrist_tolerance_pwm: int = 0,
    ) -> None:
        if kinematics is None:
            raise ValueError("an explicit kinematics backend is required")
        self.adapter = adapter
        self.kin = kinematics
        self.wrist_fixed_pwm = int(wrist_fixed_pwm)
        self.required_readback_ids = tuple(int(value) for value in required_readback_ids)
        self.pose_readback_ids = (0, 1, 2, 3, 4)
        self.servo_pwm_limits = tuple(
            (int(bounds[0]), int(bounds[1])) for bounds in servo_pwm_limits
        )
        self.wrist_tolerance_pwm = int(wrist_tolerance_pwm)
        if self.required_readback_ids != tuple(range(6)):
            raise ValueError("dynamic grasp requires PRAD for Servo000..005")
        if len(self.servo_pwm_limits) != 6 or any(
            lo > hi for lo, hi in self.servo_pwm_limits
        ):
            raise ValueError("servo_pwm_limits must contain six ordered ranges")
        if self.wrist_tolerance_pwm < 0:
            raise ValueError("wrist_tolerance_pwm must be non-negative")
        if not (
            self.servo_pwm_limits[4][0]
            <= self.wrist_fixed_pwm
            <= self.servo_pwm_limits[4][1]
        ):
            raise ValueError("wrist_fixed_pwm is outside Servo004 safety limits")
        self.last_ik: Optional[object] = None
        self.reference_tool_matrix = (
            None
            if reference_tool_matrix is None
            else validate_rigid_transform(
                reference_tool_matrix, "legacy_reference_tool_matrix"
            ).copy()
        )

    def _validate_assignments(self, assignments) -> Mapping[int, int]:
        normalized = {int(key): int(value) for key, value in assignments.items()}
        if not normalized:
            raise ValueError("motion requires at least one servo assignment")
        for servo_id, value in normalized.items():
            if servo_id < 0 or servo_id >= len(self.servo_pwm_limits):
                raise ValueError("unknown servo id {}".format(servo_id))
            lo, hi = self.servo_pwm_limits[servo_id]
            if value < lo or value > hi:
                raise MotionSafetyError(
                    "Servo{:03d} PWM {} outside safety range [{}, {}]".format(
                        servo_id, value, lo, hi
                    )
                )
        if 4 in normalized and normalized[4] != self.wrist_fixed_pwm:
            raise MotionSafetyError(
                "Servo004 must remain at PWM {}".format(self.wrist_fixed_pwm)
            )
        # Every physical action also holds and verifies the camera-independent
        # wrist rotor at its frozen position.
        normalized[4] = self.wrist_fixed_pwm
        return dict(sorted(normalized.items()))

    def _assert_wrist_snapshot(self, snapshot: PWMReadbackSnapshot) -> None:
        actual = snapshot.pwms.get(4)
        if actual is None:
            raise MotionSafetyError("Servo004 PRAD value is missing")
        if abs(int(actual) - self.wrist_fixed_pwm) > self.wrist_tolerance_pwm:
            raise MotionSafetyError(
                "Servo004 measured PWM {} differs from required {}".format(
                    actual, self.wrist_fixed_pwm
                )
            )

    def _validate_snapshot(self, snapshot: PWMReadbackSnapshot) -> PWMReadbackSnapshot:
        self._assert_wrist_snapshot(snapshot)
        for servo_id, value in snapshot.pwms.items():
            lo, hi = self.servo_pwm_limits[int(servo_id)]
            if int(value) < lo or int(value) > hi:
                raise MotionSafetyError(
                    "Servo{:03d} measured PWM {} outside safety range [{}, {}]".format(
                        int(servo_id), int(value), lo, hi
                    )
                )
        return snapshot

    def get_actual_wrist_pwm_snapshot(self) -> PWMReadbackSnapshot:
        """Read only joints that can affect the wrist/camera pose.

        This is for non-moving observation/diagnostics only. Every motion
        command and every closed-loop motion stage still requires the strict
        Servo000..005 snapshot through :meth:`get_actual_pwm_snapshot`.
        """

        snapshot = self.adapter.read_required_pwms(self.pose_readback_ids)
        return self._validate_snapshot(snapshot)

    def get_observation_pwm_snapshot(self) -> PWMReadbackSnapshot:
        """Prefer all six PRAD values, with a read-only Servo005 fallback.

        A gripper-only readback outage cannot corrupt ``T_base_wrist`` or
        ``T_base_camera``. Pure observation may therefore continue with
        Servo000..004 while recording Servo005 as missing. Missing any pose
        joint still fails closed, and motion never calls this fallback.
        """

        try:
            return self.get_actual_pwm_snapshot()
        except PWMReadbackError as exc:
            if set(exc.missing_ids) != {5}:
                raise
            return self.get_actual_wrist_pwm_snapshot()

    def get_actual_pwm_snapshot(self) -> PWMReadbackSnapshot:
        snapshot = self.adapter.read_required_pwms(self.required_readback_ids)
        return self._validate_snapshot(snapshot)

    def get_actual_wrist_pose(
        self, snapshot: Optional[PWMReadbackSnapshot] = None
    ) -> ActualArmPose:
        measured = self.get_actual_pwm_snapshot() if snapshot is None else snapshot
        self._assert_wrist_snapshot(measured)
        matrix = self.kin.forward_wrist_matrix_from_pwm(
            measured.ordered((0, 1, 2, 3))
        )
        return ActualArmPose(matrix, measured, "T_base_wrist")

    def get_actual_tcp_pose(
        self,
        T_wrist_tcp: np.ndarray,
        snapshot: Optional[PWMReadbackSnapshot] = None,
        tcp_name: str = "closed",
    ) -> ActualArmPose:
        wrist = self.get_actual_wrist_pose(snapshot)
        wrist_tcp = validate_rigid_transform(T_wrist_tcp, "T_wrist_tcp")
        return ActualArmPose(
            wrist.matrix @ wrist_tcp,
            wrist.snapshot,
            "T_base_tcp_{}".format(tcp_name),
            tcp_name=str(tcp_name),
        )

    def current_tool_matrix_from_last_command(self) -> np.ndarray:
        """Legacy diagnostic kept for old dry-run tools only.

        Real closed-loop code must call :meth:`get_actual_tcp_pose` with a
        PRAD snapshot and an explicit open/closed TCP transform.
        """

        warnings.warn(
            "commanded pose is not measured pose; use get_actual_tcp_pose",
            DeprecationWarning,
            stacklevel=2,
        )
        if not self.adapter.dry_run:
            raise MotionSafetyError("commanded pose is forbidden in real mode")
        if self.last_ik is not None and getattr(self.last_ik, "tool_matrix", None) is not None:
            return np.asarray(self.last_ik.tool_matrix, dtype=float).copy()
        if self.reference_tool_matrix is not None:
            return self.reference_tool_matrix.copy()
        raise RuntimeError("no dry-run diagnostic tool matrix is available")

    def pack_ik_command(
        self,
        ik,
        duration_ms: int,
        gripper_pwm: Optional[int] = None,
        include_gripper: bool = False,
    ) -> str:
        if ik is None:
            raise ValueError("cannot pack an empty IK result")
        if isinstance(ik, OfficialIKResult):
            if include_gripper or gripper_pwm is not None:
                raise ValueError(
                    "official IK controls Servo000..003; command Servo005 separately"
                )
            assignments = {
                servo_id: pwm for servo_id, pwm in enumerate(ik.servo_pwms)
            }
        else:
            servo_pwms = getattr(ik, "servo_pwms", None)
            if servo_pwms is not None:
                values = list(servo_pwms)
                assignments = dict(enumerate(values[:5]))
                if gripper_pwm is not None:
                    assignments[5] = int(gripper_pwm)
                elif include_gripper and len(values) >= 6:
                    assignments[5] = int(values[5])
            else:
                assignments = {
                    mapping.servo_id: mapping.to_pwm(rad)
                    for rad, mapping in zip(ik.joints_rad[:4], self.adapter.joint_maps[:4])
                }
        return self.adapter.pack_partial_pwm_command(
            self._validate_assignments(assignments), duration_ms
        )

    def set_reference_tool_matrix(self, matrix: np.ndarray) -> None:
        if not self.adapter.dry_run:
            raise MotionSafetyError("legacy reference pose is dry-run only")
        self.reference_tool_matrix = validate_rigid_transform(
            matrix, "legacy_reference_tool_matrix"
        ).copy()
        self.last_ik = None

    def execute_assignments(
        self, assignments, duration_ms: int, ik=None
    ) -> MotionResult:
        try:
            normalized = self._validate_assignments(assignments)
            servo_result = self.adapter.send_and_wait_readback(
                normalized,
                int(duration_ms),
                required_ids=self.required_readback_ids,
            )
            result = MotionResult.from_servo_result(servo_result, ik=ik)
            if result.readback_snapshot is not None:
                self._assert_wrist_snapshot(result.readback_snapshot)
            if result.ok:
                self.last_ik = ik
            return result
        except Exception as exc:
            return MotionResult(
                ok=False,
                ik=ik,
                reason=str(exc),
                motion_end_monotonic=time.monotonic(),
                simulated=self.adapter.dry_run,
            )

    def execute_ik(self, ik, duration_ms: int) -> MotionResult:
        """Execute IK and accept completion only after the PRAD gate."""

        if ik is None:
            return MotionResult(False, None, reason="cannot execute an empty IK result")
        servo_pwms = getattr(ik, "servo_pwms", None)
        if servo_pwms is None:
            assignments = {
                mapping.servo_id: mapping.to_pwm(rad)
                for rad, mapping in zip(ik.joints_rad[:4], self.adapter.joint_maps[:4])
            }
        else:
            values = list(servo_pwms)
            assignments = dict(enumerate(values[:4]))
        return self.execute_assignments(assignments, duration_ms, ik=ik)

    def move_tcp_pose(
        self,
        target_T_base_tcp: np.ndarray,
        T_wrist_tcp: np.ndarray,
        duration_ms: int = 1000,
        tcp_name: str = "closed",
    ) -> MotionResult:
        try:
            ik = self.kin.inverse_tcp_pose(
                target_T_base_tcp=target_T_base_tcp,
                T_wrist_tcp=T_wrist_tcp,
                tcp_name=tcp_name,
            )
        except Exception as exc:
            return MotionResult(False, None, reason="IK input rejected: {}".format(exc))
        if ik is None:
            return MotionResult(False, None, reason="TCP IK failed")
        return self.execute_ik(ik, duration_ms)

    def move_tcp_xyz(
        self,
        xyz_m: Iterable[float],
        pitch_deg: float,
        T_wrist_tcp: np.ndarray,
        duration_ms: int = 1000,
        tcp_name: str = "closed",
    ) -> MotionResult:
        xyz = tuple(float(value) for value in xyz_m)
        try:
            ik = self.kin.inverse_tcp_pose(
                target_xyz_m=xyz,
                pitch_deg=float(pitch_deg),
                T_wrist_tcp=T_wrist_tcp,
                tcp_name=tcp_name,
            )
        except Exception as exc:
            return MotionResult(False, None, reason="IK input rejected: {}".format(exc))
        if ik is None:
            return MotionResult(
                False,
                None,
                reason="TCP IK failed for xyz={} pitch={}".format(list(xyz), pitch_deg),
            )
        return self.execute_ik(ik, duration_ms)

    def move_gripper(self, pwm: int, duration_ms: int) -> MotionResult:
        return self.execute_assignments({5: int(pwm)}, duration_ms)

    def move_xyz(
        self,
        xyz_m: Iterable[float],
        pitch_deg: float = 70.0,
        roll_rad: float = -0.05,
        gripper: float = 0.80,
        duration_ms: int = 1000,
        gripper_pwm: Optional[int] = None,
        include_gripper: bool = False,
    ) -> MotionResult:
        """Legacy dry-run-only entrypoint retained for rollback diagnostics."""

        del roll_rad, gripper
        if not self.adapter.dry_run:
            return MotionResult(
                False,
                None,
                reason="legacy move_xyz is forbidden in real dynamic grasp mode",
            )
        if include_gripper or gripper_pwm is not None:
            return MotionResult(
                False,
                None,
                reason="move arm and gripper in separate gated stages",
                simulated=True,
            )
        ik = self.kin.inverse_pose(xyz_m, pitch_deg=pitch_deg)
        if ik is None:
            return MotionResult(False, None, reason="legacy IK failed", simulated=True)
        return self.execute_ik(ik, duration_ms)
