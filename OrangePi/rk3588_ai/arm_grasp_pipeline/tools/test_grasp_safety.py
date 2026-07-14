#!/usr/bin/env python3
"""Hardware-free checks for target centering, depth stability, and plan safety."""
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.arm_motion import ArmMotion
from arm_grasp_pipeline.geometry import CameraIntrinsics
from arm_grasp_pipeline.grasp_state_machine import GraspConfig, GraspState, GraspStateMachine
from arm_grasp_pipeline.official_kinematics import OfficialArmKinematics
from arm_grasp_pipeline.serial_servo_adapter import SerialServoArmAdapter
from arm_grasp_pipeline.target_depth import BBox


def make_machine():
    adapter = SerialServoArmAdapter(dry_run=True)
    kin = OfficialArmKinematics()
    reference = kin.estimate_tool_matrix_from_pwm((1380, 1909, 1900, 620, 1500, 1500))
    arm = ArmMotion(adapter, kinematics=kin, reference_tool_matrix=reference)
    intr = CameraIntrinsics(fx=610.0, fy=610.0, cx=320.0, cy=240.0)
    cfg = GraspConfig(stable_frames=5, depth_stable_frames=4,
                      pre_grasp_standoff_m=0.04, pitch_deg=20.0, lift_pitch_deg=0.0)
    return GraspStateMachine(arm, intr, cfg=cfg)


def feed_boxes(machine, box):
    for _ in range(machine.cfg.stable_frames + 1):
        machine.update_detection(box)


def depth_frame(value):
    frame = np.zeros((480, 640), dtype=np.float32)
    frame[180:300, 260:380] = float(value)
    return frame


def main() -> int:
    machine = make_machine()

    feed_boxes(machine, BBox(20, 180, 120, 300, 0.9, "bottle"))
    for _ in range(machine.cfg.depth_stable_frames):
        assert machine.try_lock_depth(depth_frame(0.32)) is None

    machine.update_detection(None)
    feed_boxes(machine, BBox(280, 200, 360, 280, 0.9, "bottle"))
    for value in (0.30, 0.35, 0.30, 0.35):
        assert machine.try_lock_depth(depth_frame(value)) is None

    machine.update_detection(None)
    feed_boxes(machine, BBox(280, 200, 360, 280, 0.9, "bottle"))
    target = None
    for value in (0.320, 0.321, 0.319, 0.320):
        target = machine.try_lock_depth(depth_frame(value))
    assert target is not None

    machine.locked_target_base = np.array([0.28, 0.04, 0.12], dtype=float)
    plan = machine.plan_locked_grasp()
    assert [row[0] for row in plan] == [
        GraspState.PRE_GRASP, GraspState.APPROACH, GraspState.CLOSE, GraspState.LIFT]
    pre, grasp = plan[0][1], plan[1][1]
    target = machine.locked_target_base
    approach_axis = np.array([target[0], target[1], 0.0], dtype=float)
    approach_axis /= np.linalg.norm(approach_axis)
    assert np.allclose(pre, target - approach_axis * machine.cfg.pre_grasp_standoff_m)
    assert np.allclose(grasp, target + approach_axis * machine.cfg.grasp_insert_m)
    assert pre[2] == target[2] and grasp[2] == target[2]
    assert plan[0][2] == 600 and plan[2][2] == 2400

    machine.locked_target_base = np.array([0.80, 0.0, 0.12], dtype=float)
    try:
        machine.plan_locked_grasp()
    except ValueError as exc:
        assert "outside workspace" in str(exc)
    else:
        raise AssertionError("workspace guard did not reject unreachable target")

    print("GRASP_SAFETY_CHECK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
