#!/usr/bin/env python3
"""C-5.2.4 hardware-free regression suite."""
from __future__ import annotations

import math
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.arm_motion import ArmMotion
from arm_grasp_pipeline.fixed_view import (
    FixedViewCalibration,
    ObjectGeometry,
    fixed_view_target_debug,
    median_depth_around_pixel,
    pre_grasp_from_bottle_center,
    solve_rigid_transform,
)
from arm_grasp_pipeline.geometry import CameraIntrinsics, depth_pixel_to_camera
from arm_grasp_pipeline.grasp_planner import (
    GraspConfig,
    GraspState,
    build_fixed_view_grasp_plan,
)
from arm_grasp_pipeline.grasp_state_machine import GraspStateMachine
from arm_grasp_pipeline.official_kinematics import OfficialIKResult
from arm_grasp_pipeline.tools.d435_yolo_grasp import validate_real_grasp_request
from arm_grasp_pipeline.tools.collect_base_camera_points import (
    parse_base_xyz_mm,
    pose_mismatches,
)
from arm_grasp_pipeline.target_depth import BBox, median_depth_in_bbox


class FakeKinematics:
    def __init__(self, reject=False):
        self.reject = bool(reject)

    def inverse_pose(self, xyz_m, pitch_deg=None, roll_rad=-0.05, gripper=0.0):
        del roll_rad, gripper
        if self.reject:
            return None
        xyz = tuple(float(value) for value in xyz_m)
        pitch = float(0.0 if pitch_deg is None else pitch_deg)
        tool = np.eye(4, dtype=float)
        tool[:3, 3] = xyz
        return OfficialIKResult(
            joints_rad=(0.0, 0.0, 0.0, 0.0),
            final_pitch_deg=pitch,
            target_xyz_m=xyz,
            servo_angles_deg=(0.0, 0.0, 0.0, 0.0),
            servo_pwms=(1500, 1500, 1500, 1500),
            tool_matrix=tool,
        )


class RecordingAdapter:
    dry_run = True

    def __init__(self):
        self.commands = []

    def send_partial_pwm_command(self, assignments, duration_ms=1000):
        normalized = {int(key): int(value) for key, value in assignments.items()}
        self.commands.append(("partial", normalized, int(duration_ms)))
        return str(normalized)

    def send_pwm_command(self, values, duration_ms=1000):
        normalized = tuple(int(value) for value in values)
        self.commands.append(("full", normalized, int(duration_ms)))
        return str(normalized)


def proper_rotation():
    ax, ay, az = [math.radians(value) for value in (13.0, -8.0, 21.0)]
    rx = np.array([[1, 0, 0], [0, math.cos(ax), -math.sin(ax)],
                   [0, math.sin(ax), math.cos(ax)]], dtype=float)
    ry = np.array([[math.cos(ay), 0, math.sin(ay)], [0, 1, 0],
                   [-math.sin(ay), 0, math.cos(ay)]], dtype=float)
    rz = np.array([[math.cos(az), -math.sin(az), 0],
                   [math.sin(az), math.cos(az), 0], [0, 0, 1]], dtype=float)
    return rz @ ry @ rx


def real_args(**overrides):
    values = {
        "dry_run": False,
        "execute_on_lock": True,
        "enable_arm": True,
        "auto_center": False,
        "joint_pwm_calibrated": True,
        "current_pwms": "",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def real_config(reference=None):
    reference = reference or [1380, 1909, 1900, 620, 1500, 1500]
    return {
        "serial": {"joint_pwm_calibrated": True},
        "kinematics": {"calibrated": True},
        "camera_mount": {
            "frozen": True,
            "requires_fixed_servo004": True,
            "fixed_servo004_pwm": 1500,
        },
        "grasp": {
            "wrist_fixed_pwm": 1500,
            "retry_pose_pwms": list(reference),
        },
    }


class FixedViewGraspTests(unittest.TestCase):
    def test_calibration_collector_converts_base_mm_to_metres(self):
        self.assertTrue(np.allclose(
            parse_base_xyz_mm("230,-60,85"),
            (0.230, -0.060, 0.085),
        ))

    def test_reference_pose_verification_requires_servo000_through_004(self):
        reference = [1380, 1909, 1900, 620, 1500, 1500]
        actual = {0: 1382, 1: 1913, 2: 1901, 3: 620, 4: 1500, 5: None}
        self.assertEqual(pose_mismatches(reference, actual, 30), {})
        actual[4] = 1450
        self.assertIn(4, pose_mismatches(reference, actual, 30))

    def test_repository_config_uses_local_unapproved_link_measurements(self):
        with (ROOT / "config/arm_grasp_default.json").open(
                "r", encoding="utf-8") as handle:
            config = json.load(handle)
        kinematics = config["kinematics"]
        self.assertFalse(kinematics["calibrated"])
        self.assertEqual(
            [kinematics[name] for name in ("l0_m", "l1_m", "l2_m", "l3_m")],
            [0.100, 0.130, 0.065, 0.177],
        )
        self.assertIn("C-5.2.0_arm_camera_tcp_measurement_sheet.md", kinematics["source"])

    def test_known_rigid_transform_recovery(self):
        camera = np.array([
            [0.00, 0.00, 0.20], [0.04, 0.00, 0.22], [0.00, 0.05, 0.24],
            [0.03, 0.04, 0.30], [-0.02, 0.03, 0.27], [0.05, -0.02, 0.25],
        ], dtype=float)
        rotation = proper_rotation()
        translation = np.array([0.18, -0.04, 0.09], dtype=float)
        base = (rotation @ camera.T).T + translation
        result = solve_rigid_transform(camera, base)
        self.assertTrue(np.allclose(result.matrix_4x4[:3, :3], rotation, atol=1e-10))
        self.assertTrue(np.allclose(result.matrix_4x4[:3, 3], translation, atol=1e-10))
        self.assertLess(result.rmse_m, 1e-10)
        self.assertAlmostEqual(result.determinant, 1.0, places=8)

    def test_reflection_is_rejected(self):
        camera = np.array([
            [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]
        ], dtype=float)
        base = camera.copy()
        base[:, 0] *= -1.0
        with self.assertRaisesRegex(ValueError, "reflection"):
            solve_rigid_transform(camera, base)

    def test_projection_formula(self):
        intr = CameraIntrinsics(fx=500.0, fy=400.0, cx=320.0, cy=240.0)
        point = depth_pixel_to_camera((370.0, 200.0), 0.8, intr)
        self.assertTrue(np.allclose(point, (0.08, -0.08, 0.8)))

    def test_depth_roi_filters_invalid_and_outlier_values(self):
        depth = np.full((40, 40), 0.42, dtype=float)
        depth[15:18, 15:18] = 0.0
        depth[18, 18] = np.nan
        depth[19, 19] = np.inf
        depth[20, 20] = 3.0
        depth[21, 21] = 0.01
        value = median_depth_in_bbox(depth, BBox(5, 5, 35, 35), inner_ratio=0.8)
        self.assertAlmostEqual(value, 0.42, places=8)

    def test_clicked_pixel_depth_filters_invalid_and_outlier_values(self):
        depth = np.full((5, 20, 20), 0.36, dtype=float)
        depth[:, 8:10, 8:10] = 0.0
        depth[0, 10, 10] = np.nan
        depth[1, 10, 10] = np.inf
        depth[2, 10, 10] = 3.0
        value = median_depth_around_pixel(depth, (10, 10), radius_px=4)
        self.assertAlmostEqual(value, 0.36, places=8)

    def test_camera_to_base_matrix_direction(self):
        intr = CameraIntrinsics(fx=500.0, fy=500.0, cx=320.0, cy=240.0)
        matrix = np.eye(4, dtype=float)
        matrix[:3, 3] = [0.20, 0.01, -0.10]
        debug = fixed_view_target_debug(
            (320.0, 240.0), 0.20, intr, matrix,
            ObjectGeometry(bottle_radius_m=0.032),
        )
        self.assertTrue(np.allclose(debug.point_base_surface_m, (0.20, 0.01, 0.10)))

    def test_bottle_radius_compensation_direction(self):
        intr = CameraIntrinsics(fx=500.0, fy=500.0, cx=320.0, cy=240.0)
        matrix = np.eye(4, dtype=float)
        matrix[:3, 3] = [0.20, 0.0, -0.10]
        debug = fixed_view_target_debug(
            (320.0, 240.0), 0.20, intr, matrix,
            ObjectGeometry(bottle_radius_m=0.032),
        )
        self.assertTrue(np.allclose(debug.bottle_center_base_m, (0.232, 0.0, 0.10)))

    def test_pre_grasp_distance(self):
        center = np.array([0.24, 0.06, 0.12], dtype=float)
        pre = pre_grasp_from_bottle_center(center, 0.07)
        self.assertAlmostEqual(float(np.linalg.norm(center - pre)), 0.07, places=10)
        self.assertAlmostEqual(float(pre[2]), float(center[2]), places=10)

    def test_workspace_rejection(self):
        with self.assertRaisesRegex(ValueError, "outside workspace"):
            build_fixed_view_grasp_plan(
                (0.80, 0.0, 0.12), FakeKinematics(), GraspConfig()
            )

    def test_ik_rejection(self):
        with self.assertRaisesRegex(ValueError, "no IK solution"):
            build_fixed_view_grasp_plan(
                (0.24, 0.0, 0.12), FakeKinematics(reject=True), GraspConfig()
            )

    def test_uncalibrated_real_grasp_rejection(self):
        calibration = FixedViewCalibration(
            calibrated=False,
            reference_servo_pwms=(1380, 1909, 1900, 620, 1500, 1500),
            base_to_camera_matrix_4x4=np.eye(4),
            rmse_m=0.001,
            max_error_m=0.002,
        )
        with self.assertRaisesRegex(ValueError, "calibrated is false"):
            validate_real_grasp_request(real_args(), real_config(), calibration)

    def test_calibration_error_thresholds_reject_real_grasp(self):
        calibration = FixedViewCalibration(
            calibrated=True,
            reference_servo_pwms=(1380, 1909, 1900, 620, 1500, 1500),
            base_to_camera_matrix_4x4=np.eye(4),
            rmse_m=0.011,
            max_error_m=0.016,
        )
        with self.assertRaisesRegex(ValueError, "rmse_m exceeds 0.010"):
            validate_real_grasp_request(real_args(), real_config(), calibration)

    def test_non_finite_calibration_limit_cannot_bypass_real_gate(self):
        calibration = FixedViewCalibration(
            calibrated=True,
            reference_servo_pwms=(1380, 1909, 1900, 620, 1500, 1500),
            base_to_camera_matrix_4x4=np.eye(4),
            rmse_m=0.001,
            max_error_m=0.002,
            max_rmse_m=float("nan"),
        )
        with self.assertRaisesRegex(ValueError, "max_rmse_m must be positive and finite"):
            validate_real_grasp_request(real_args(), real_config(), calibration)

    def test_unmeasured_kinematics_rejects_real_grasp(self):
        calibration = FixedViewCalibration(
            calibrated=True,
            reference_servo_pwms=(1380, 1909, 1900, 620, 1500, 1500),
            base_to_camera_matrix_4x4=np.eye(4),
            rmse_m=0.001,
            max_error_m=0.002,
        )
        config = real_config()
        config["kinematics"]["calibrated"] = False
        with self.assertRaisesRegex(ValueError, "kinematics.calibrated is false"):
            validate_real_grasp_request(real_args(), config, calibration)

    def test_max_stage_pre_grasp_sends_no_approach(self):
        adapter = RecordingAdapter()
        arm = ArmMotion(adapter, kinematics=FakeKinematics())
        machine = GraspStateMachine(
            arm,
            CameraIntrinsics(500.0, 500.0, 320.0, 240.0),
            np.eye(4),
            cfg=GraspConfig(motion_settle_s=0.0),
            object_geometry=ObjectGeometry(),
        )
        machine.locked_target_base = np.array([0.24, 0.0, 0.12], dtype=float)
        self.assertTrue(machine.execute_locked_grasp(max_stage="pre_grasp"))
        arm_commands = [entry for entry in adapter.commands
                        if entry[0] == "partial" and set(entry[1]) == {0, 1, 2, 3}]
        self.assertEqual(len(arm_commands), 1)
        self.assertEqual(machine.state, GraspState.VERIFY)

    def test_servo004_not_1500_rejects_real_grasp(self):
        reference = (1380, 1909, 1900, 620, 1490, 1500)
        calibration = FixedViewCalibration(
            calibrated=True,
            reference_servo_pwms=reference,
            base_to_camera_matrix_4x4=np.eye(4),
            rmse_m=0.001,
            max_error_m=0.002,
        )
        with self.assertRaisesRegex(ValueError, "Servo004"):
            validate_real_grasp_request(
                real_args(), real_config(reference=list(reference)), calibration
            )

    def test_five_observations_produce_distinct_base_targets(self):
        intr = CameraIntrinsics(fx=500.0, fy=500.0, cx=320.0, cy=240.0)
        matrix = np.eye(4, dtype=float)
        matrix[:3, 3] = [0.20, 0.0, -0.10]
        observations = [
            ((280, 220), 0.24), ((300, 240), 0.25), ((320, 260), 0.26),
            ((340, 230), 0.27), ((360, 250), 0.28),
        ]
        targets = [
            fixed_view_target_debug(pixel, depth, intr, matrix, ObjectGeometry()).bottle_center_base_m
            for pixel, depth in observations
        ]
        rounded = {tuple(round(value, 6) for value in target) for target in targets}
        self.assertEqual(len(rounded), 5)

    def test_approach_is_horizontal_and_waypoint_limited(self):
        config = GraspConfig(
            pre_grasp_standoff_m=0.07,
            approach_waypoint_spacing_m=0.01,
        )
        plan = build_fixed_view_grasp_plan((0.24, 0.03, 0.12), FakeKinematics(), config)
        pre = np.asarray([step for step in plan if step.state == GraspState.PRE_GRASP][0].xyz_m)
        approach = [step for step in plan if step.state == GraspState.APPROACH]
        points = [pre] + [np.asarray(step.xyz_m) for step in approach]
        for first, second in zip(points, points[1:]):
            self.assertLessEqual(float(np.linalg.norm(second - first)), 0.0100001)
            self.assertAlmostEqual(float(second[2]), float(first[2]), places=10)


if __name__ == "__main__":
    unittest.main(verbosity=2)
