#!/usr/bin/env python3
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.arm_motion import ArmMotion
from arm_grasp_pipeline.serial_servo_adapter import SerialServoArmAdapter
from arm_grasp_pipeline.geometry import CameraIntrinsics
from arm_grasp_pipeline.target_depth import BBox
from arm_grasp_pipeline.grasp_state_machine import GraspStateMachine

adapter = SerialServoArmAdapter(dry_run=True)
arm = ArmMotion(adapter)
intr = CameraIntrinsics(fx=610, fy=610, cx=320, cy=240)
gsm = GraspStateMachine(arm, intr)

depth = np.zeros((480, 640), dtype=np.float32)
depth[200:280, 280:360] = 0.32
for _ in range(6):
    gsm.update_detection(BBox(280, 200, 360, 280, 0.90, "bottle"))

target = gsm.try_lock_depth(depth)
print("locked_target_base_from_depth:", target)
# Hardware-free dry run: use a reachable calibrated target to verify IK + command packing.
gsm.locked_target_base = np.array([0.16, 0.00, 0.12], dtype=float)
print("locked_target_base_for_mock_cycle:", gsm.locked_target_base)
print("execute:", gsm.execute_locked_grasp())
