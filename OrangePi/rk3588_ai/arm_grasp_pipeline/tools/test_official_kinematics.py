#!/usr/bin/env python3
"""Regression checks for the STM32F103 official arm kinematics port."""
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.official_kinematics import OfficialArmKinematics, PWM_PER_DEG
from arm_grasp_pipeline.arm_motion import ArmMotion
from arm_grasp_pipeline.serial_servo_adapter import SerialServoArmAdapter


def main() -> int:
    kin = OfficialArmKinematics()
    assert abs(PWM_PER_DEG - (2200.0 / 270.0)) < 1e-12
    assert kin._pwm_targets((30.0, 0.0, 0.0, 0.0))[0] == 1744
    assert kin._pwm_targets((90.0, 0.0, 0.0, 0.0))[0] == 2233
    assert kin._pwm_targets((-90.0, 0.0, 0.0, 0.0))[0] == 767
    assert kin._pwm_targets((0.0, 30.0, 30.0, 30.0)) == (1500, 1256, 1744, 1744)
    semantic = (30.0, -40.0, 45.0, -60.0)
    pwms = kin._pwm_targets(semantic)
    recovered = kin._angles_from_pwm(pwms)
    assert np.allclose(recovered, semantic, atol=0.07), (semantic, pwms, recovered)
    for xyz in ((0.18, 0.00, 0.12), (0.22, 0.05, 0.10), (0.14, -0.04, 0.16)):
        result = kin.inverse_pose(xyz, gripper=0.8)
        assert result is not None, xyz
        assert len(result.servo_pwms) == 4
        forward = kin.estimate_tool_matrix_from_pwm(result.servo_pwms)
        assert np.linalg.norm(forward[:3, 3] - np.asarray(xyz)) < 0.003, (xyz, forward[:3, 3])
        assert all(500 <= value <= 2490 for value in result.servo_pwms)

    fixed_pitch = kin.inverse_pose((0.25, 0.04, 0.13), pitch_deg=20.0)
    assert fixed_pitch is not None
    # Final pitch is q3 + 90 - q1 - q2.  Each of those three joints is
    # rounded to an integer PWM, so allow exactly the summed half-PWM angular
    # quantisation bound rather than requiring impossible floating equality.
    pitch_quantization_tolerance_deg = sum(
        0.5 / kin.pwm_per_deg_by_joint[index] for index in (1, 2, 3)
    )
    pitch_error_deg = abs(fixed_pitch.final_pitch_deg - 20.0)
    assert pitch_error_deg <= pitch_quantization_tolerance_deg + 1e-9, (
        pitch_error_deg,
        pitch_quantization_tolerance_deg,
        fixed_pitch.servo_pwms,
    )

    assert kin.inverse_pose((0.50, 0.0, 0.10)) is None
    level_tool = kin._tool_matrix((0.20, 0.0, 0.10), 0.0)
    assert np.allclose(level_tool[:3, :3], np.eye(3), atol=1e-9)
    reference = kin.estimate_tool_matrix_from_pwm((1500, 1907, 1900, 900, 1500, 1500))
    assert reference.shape == (4, 4)
    assert np.all(np.isfinite(reference))

    adapter = SerialServoArmAdapter(dry_run=True)
    assert adapter.pack_kinematics_command((0.200, 0.030, 0.150), 1200) == \
        "$KMS:30.0,200.0,150.0,1200!"
    arm = ArmMotion(adapter, kinematics=kin, reference_tool_matrix=reference)
    result = kin.inverse_pose((0.180, 0.0, 0.120))
    command = arm.pack_ik_command(result, 1000, include_gripper=False)
    expected_assignments = {
        servo_id: pwm for servo_id, pwm in enumerate(result.servo_pwms)
    }
    # Every physical arm command explicitly holds the camera-independent
    # Servo004 rotor at its frozen PWM, even when Servo005 is omitted.
    expected_assignments[4] = arm.wrist_fixed_pwm
    expected = adapter.pack_partial_pwm_command(
        expected_assignments,
        1000,
    )
    assert command == expected
    assert command.startswith("{#000P") and "#003P" in command
    assert "#004P1500" in command and "#005" not in command

    try:
        arm.pack_ik_command(result, 1000, gripper_pwm=1000, include_gripper=False)
    except ValueError as exc:
        assert "Servo000..003" in str(exc)
    else:
        raise AssertionError("official IK unexpectedly accepted a gripper command")
    print("OFFICIAL_KINEMATICS_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
