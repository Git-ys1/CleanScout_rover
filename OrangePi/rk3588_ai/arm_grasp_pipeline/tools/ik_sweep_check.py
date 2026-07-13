#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.official_kinematics import OfficialArmKinematics

kin = OfficialArmKinematics()
tests = [
    (0.16, 0.00, 0.16),
    (0.20, 0.04, 0.15),
    (0.18, -0.06, 0.14),
    (0.12, 0.00, 0.12),
]
for xyz in tests:
    ans = kin.inverse_pose(xyz)
    print(
        xyz,
        "=>",
        None if ans is None else list(ans.servo_pwms),
        "alpha",
        None if ans is None else -ans.final_pitch_deg,
    )
