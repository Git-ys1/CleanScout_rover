#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.kinematics_5dof import Arm5DoFKinematics

kin = Arm5DoFKinematics()
tests = [
    (0.16, 0.00, 0.16),
    (0.20, 0.04, 0.15),
    (0.18, -0.06, 0.14),
    (0.12, 0.00, 0.12),
]
for xyz in tests:
    ans = kin.inverse_pose(xyz, pitch_deg=70)
    print(xyz, "=>", None if ans is None else [round(v, 4) for v in ans.joints_rad], "pitch", None if ans is None else ans.final_pitch_deg)
