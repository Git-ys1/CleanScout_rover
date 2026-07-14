#!/usr/bin/env python3
from pathlib import Path
import argparse
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.arm_motion import ArmMotion
from arm_grasp_pipeline.official_kinematics import OfficialArmKinematics
from arm_grasp_pipeline.serial_servo_adapter import SerialServoArmAdapter
from arm_grasp_pipeline.geometry import CameraIntrinsics
from arm_grasp_pipeline.fixed_view import ObjectGeometry
from arm_grasp_pipeline.target_depth import BBox
from arm_grasp_pipeline.grasp_state_machine import GraspStateMachine
from arm_grasp_pipeline.ros_compat import PrintRosBridge


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--print_ros", action="store_true", help="print ROS-compatible dataclass payloads")
    args = ap.parse_args()

    adapter = SerialServoArmAdapter(dry_run=True)
    kin = OfficialArmKinematics()
    arm = ArmMotion(adapter, kinematics=kin)
    intr = CameraIntrinsics(fx=610, fy=610, cx=320, cy=240)
    event_sink = PrintRosBridge() if args.print_ros else None
    T_base_camera = np.array([
        [0.0, 0.0, 1.0, -0.120],
        [-1.0, 0.0, 0.0, 0.0],
        [0.0, -1.0, 0.0, 0.120],
        [0.0, 0.0, 0.0, 1.0],
    ], dtype=float)
    gsm = GraspStateMachine(
        arm, intr, T_base_camera, object_geometry=ObjectGeometry(), event_sink=event_sink
    )

    depth = np.zeros((480, 640), dtype=np.float32)
    depth[200:280, 280:360] = 0.32
    for _ in range(6):
        gsm.update_detection(BBox(280, 200, 360, 280, 0.90, "bottle"))

    target = None
    for _ in range(gsm.cfg.depth_stable_frames):
        target = gsm.try_lock_depth(depth)
    print("locked_target_base_from_depth:", target)
    # Hardware-free dry run: use a reachable target to verify IK + command packing.
    gsm.locked_target_base = np.array([0.25, 0.00, 0.18], dtype=float)
    print("locked_target_base_for_mock_cycle:", gsm.locked_target_base)
    print("execute:", gsm.execute_locked_grasp())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
