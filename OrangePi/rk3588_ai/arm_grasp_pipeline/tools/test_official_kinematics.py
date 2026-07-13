#!/usr/bin/env python3
"""Regression checks for the STM32F103 official arm kinematics port."""
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.official_kinematics import OfficialArmKinematics


def main() -> int:
    kin = OfficialArmKinematics()
    for xyz in ((0.18, 0.00, 0.12), (0.22, 0.05, 0.10), (0.14, -0.04, 0.16)):
        result = kin.inverse_pose(xyz, gripper=0.8)
        assert result is not None, xyz
        forward = kin.forward_matrix_from_pwm(result.servo_pwms)
        assert np.linalg.norm(forward[:3, 3] - np.asarray(xyz)) < 0.003, (xyz, forward[:3, 3])
        assert all(500 <= value <= 2500 for value in result.servo_pwms)

    assert kin.inverse_pose((0.50, 0.0, 0.10)) is None
    reference = kin.forward_matrix_from_pwm((1500, 1907, 1900, 900, 1500, 1500))
    assert reference.shape == (4, 4)
    assert np.all(np.isfinite(reference))
    print("OFFICIAL_KINEMATICS_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
