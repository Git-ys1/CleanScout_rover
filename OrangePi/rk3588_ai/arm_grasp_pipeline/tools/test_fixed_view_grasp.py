#!/usr/bin/env python3
"""C-5.2.5 hardware-free regression suite."""
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
    rebase_base_camera_for_base_yaw,
    solve_rigid_transform,
)
from arm_grasp_pipeline.geometry import CameraIntrinsics, depth_pixel_to_camera
from arm_grasp_pipeline.grasp_planner import (
    GraspConfig,
    GraspState,
    build_fixed_view_grasp_plan,
)
from arm_grasp_pipeline.official_kinematics import (
    OfficialArmKinematics,
    OfficialIKResult,
)
from arm_grasp_pipeline.rknn_yolo_detector import RknnYolo11Detector
from arm_grasp_pipeline.tools.d435_yolo_grasp import (
    expected_stage_pwms,
    reference_pose_mismatches,
    validate_real_grasp_request,
)
from arm_grasp_pipeline.tools.validate_fixed_view_target import (
    minimum_reachable_center_radius,
)
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
    reference = reference or [1500, 1909, 1900, 620, 1500, 1500]
    return {
        "serial": {"joint_pwm_calibrated": True},
        "kinematics": {
            "backend": "official_f103_dynamic_wrist",
            "calibrated": True,
            "l0_m": 0.100,
            "l1_m": 0.130,
            "l2_m": 0.065,
            "wrist_link_m": 0.055,
            "measured_l3_total_closed_m": 0.190,
            "closed_tcp_axial_from_wrist_m": 0.135,
        },
        "joint_pwm_calibration": {
            "calibrated": True,
            "raw_pwm_min": 500,
            "raw_pwm_max": 2700,
            "travel_deg": 270.0,
            "zero_pwms": [1500, 1500, 1500, 1500],
            "pwm_signs": [1, -1, 1, 1],
            "pwm_per_deg_by_joint": [
                8.148148148148149,
                7.0908242948362,
                7.93582743625423,
                6.478095739111546,
            ],
            "command_pwm_min": 500,
            "command_pwm_max": 2490,
        },
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
    def test_detector_threshold_is_configurable_before_runtime_start(self):
        detector = RknnYolo11Detector("model.rknn", ".", object_threshold=0.15)
        self.assertAlmostEqual(detector.object_threshold, 0.15)
        with self.assertRaisesRegex(ValueError, "object_threshold"):
            RknnYolo11Detector("model.rknn", ".", object_threshold=0.0)

    def test_calibration_collector_converts_base_mm_to_metres(self):
        self.assertTrue(np.allclose(
            parse_base_xyz_mm("230,-60,85"),
            (0.230, -0.060, 0.085),
        ))

    def test_reference_pose_verification_requires_servo000_through_004(self):
        reference = [1500, 1909, 1900, 620, 1500, 1500]
        actual = {0: 1502, 1: 1913, 2: 1901, 3: 620, 4: 1500, 5: None}
        self.assertEqual(pose_mismatches(reference, actual, 30), {})
        actual[4] = 1450
        self.assertIn(4, pose_mismatches(reference, actual, 30))

    def test_runtime_reference_pose_readback_requires_all_six_servos(self):
        reference = [1500, 1909, 1900, 620, 1500, 1500]
        actual = {index: value for index, value in enumerate(reference)}
        self.assertEqual(reference_pose_mismatches(reference, actual, 40), {})
        actual[3] = 700
        self.assertIn("3", reference_pose_mismatches(reference, actual, 40))
        actual[3] = 620
        actual[5] = None
        self.assertIn("5", reference_pose_mismatches(reference, actual, 40))

    def test_stage_readback_uses_last_waypoint_and_ignores_gripper_for_arm_gate(self):
        plan = [
            {"state": "APPROACH", "servo_pwms_000_005": [1500, 1600, 1700, 1800, 1500, 1000]},
            {"state": "APPROACH", "servo_pwms_000_005": [1510, 1610, 1710, 1810, 1500, 1000]},
            {"state": "CLOSE", "servo_pwms_000_005": [1510, 1610, 1710, 1810, 1500, 2000]},
        ]
        expected = expected_stage_pwms(plan, "approach")
        self.assertEqual(expected, [1510, 1610, 1710, 1810, 1500, 1000])
        actual = {0: 1510, 1: 1610, 2: 1710, 3: 1810, 4: 1500, 5: 1400}
        self.assertEqual(
            reference_pose_mismatches(expected, actual, 40, servo_ids=range(5)),
            {},
        )

    def test_repository_config_uses_measured_joint_mapping(self):
        with (ROOT / "config/arm_grasp_default.json").open(
                "r", encoding="utf-8") as handle:
            config = json.load(handle)
        kinematics = config["kinematics"]
        self.assertTrue(kinematics["calibrated"])
        self.assertEqual(
            [kinematics[name] for name in ("l0_m", "l1_m", "l2_m", "wrist_link_m")],
            [0.100, 0.130, 0.065, 0.055],
        )
        self.assertAlmostEqual(kinematics["measured_l3_total_closed_m"], 0.190)
        self.assertAlmostEqual(kinematics["closed_tcp_axial_from_wrist_m"], 0.135)
        self.assertIn("C-5.2.0_arm_camera_tcp_measurement_sheet.md", kinematics["source"])
        joint = config["joint_pwm_calibration"]
        self.assertTrue(joint["calibrated"])
        self.assertEqual(joint["zero_pwms"], [1500, 1500, 1500, 1500])
        self.assertEqual(joint["pwm_signs"], [1, -1, 1, 1])
        self.assertAlmostEqual(joint["pwm_per_deg"], 2200.0 / 270.0, places=12)
        self.assertEqual(joint["command_pwm_max"], 2490)
        self.assertEqual(len(joint["pwm_per_deg_by_joint"]), 4)
        self.assertAlmostEqual(joint["pwm_per_deg_by_joint"][2], 7.93582743625423)
        self.assertAlmostEqual(joint["pwm_per_deg_by_joint"][3], 6.478095739111546)

    def test_per_joint_angle_mapping_and_controller_limit(self):
        config = real_config()
        kin = OfficialArmKinematics.from_config(
            config["kinematics"], config["joint_pwm_calibration"]
        )
        pwms = kin._pwm_targets((30.0, -20.0, 50.0, -90.0))
        self.assertEqual(pwms, (1744, 1642, 1897, 917))
        self.assertTrue(np.allclose(
            kin._angles_from_pwm(pwms),
            (30.0, -20.0, 50.0, -90.0),
            atol=0.08,
        ))
        self.assertIsNone(kin._pwm_targets((0.0, 0.0, 125.0, 0.0)))

    def test_measured_reference_pose_pitch_matches_physical_observation(self):
        with (ROOT / "config/arm_grasp_default.json").open(
                "r", encoding="utf-8") as handle:
            config = json.load(handle)
        kin = OfficialArmKinematics.from_config(
            config["kinematics"], config["joint_pwm_calibration"]
        )
        tracking = kin.estimate_tool_matrix_from_pwm(
            [1500, 1909, 1900, 900, 1500, 1500]
        )
        fixed_view = kin.estimate_tool_matrix_from_pwm(
            [1500, 1909, 1900, 620, 1500, 1500]
        )
        tracking_pitch = math.degrees(math.asin(float(tracking[2, 0])))
        fixed_view_pitch = math.degrees(math.asin(float(fixed_view[2, 0])))
        self.assertLess(abs(tracking_pitch), 6.0)
        self.assertLess(fixed_view_pitch, -30.0)

    def test_horizontal_bottle_grasp_at_measured_reachable_radius(self):
        with (ROOT / "config/arm_grasp_default.json").open(
                "r", encoding="utf-8") as handle:
            config = json.load(handle)
        kin = OfficialArmKinematics.from_config(
            config["kinematics"], config["joint_pwm_calibration"]
        )
        grasp = GraspConfig.from_mapping(config["grasp"])
        plan = build_fixed_view_grasp_plan(
            (0.342, -0.014, 0.155),
            kin,
            grasp,
        )
        pre = next(step for step in plan if step.state == GraspState.PRE_GRASP)
        close = next(step for step in plan if step.state == GraspState.CLOSE)
        lift = next(step for step in plan if step.state == GraspState.LIFT)
        self.assertEqual(pre.pitch_deg, 0.0)
        self.assertEqual(pre.servo_pwms, (1481, 1292, 2488, 1914, 1500, 1112))
        self.assertEqual(close.servo_pwms, (1481, 1162, 2075, 1695, 1500, 2000))
        self.assertEqual(lift.pitch_deg, -11.0)
        self.assertEqual(lift.servo_pwms, (1481, 1185, 1820, 1537, 1500, 2000))
        self.assertLessEqual(pre.servo_pwms[2], 2490)

    def test_horizontal_reachability_hint_uses_complete_plan(self):
        with (ROOT / "config/arm_grasp_default.json").open(
                "r", encoding="utf-8") as handle:
            config = json.load(handle)
        kin = OfficialArmKinematics.from_config(
            config["kinematics"], config["joint_pwm_calibration"]
        )
        grasp = GraspConfig.from_mapping(config["grasp"])
        current = (0.24563334954400154, -0.004183836378415715, 0.1536203742911384)
        minimum = minimum_reachable_center_radius(current, grasp, kin)
        self.assertAlmostEqual(minimum, 0.343, places=3)
        self.assertGreater(minimum - math.hypot(current[0], current[1]), 0.094)

    def test_pre_grasp_stage_does_not_require_future_lift_solution(self):
        with (ROOT / "config/arm_grasp_default.json").open(
                "r", encoding="utf-8") as handle:
            config = json.load(handle)
        config["grasp"]["lift_pitch_deg"] = -10.0
        kin = OfficialArmKinematics.from_config(
            config["kinematics"], config["joint_pwm_calibration"]
        )
        grasp = GraspConfig.from_mapping(config["grasp"])
        plan = build_fixed_view_grasp_plan(
            (0.342, -0.014, 0.155),
            kin,
            grasp,
            max_stage="pre_grasp",
        )
        self.assertEqual([step.state for step in plan], [GraspState.OPEN, GraspState.PRE_GRASP])

    def test_fixed_view_matrix_rebases_with_servo000_yaw(self):
        source = np.eye(4, dtype=float)
        source[:3, 3] = [0.20, 0.0, 0.10]
        rebased = rebase_base_camera_for_base_yaw(source, 30.0)
        self.assertTrue(np.allclose(
            rebased[:3, 3],
            [0.20 * math.cos(math.radians(30.0)), 0.10, 0.10],
            atol=1e-12,
        ))
        self.assertAlmostEqual(float(np.linalg.det(rebased[:3, :3])), 1.0, places=12)

    def test_repository_reference1500_rejects_unverified_yaw_rebase(self):
        with (ROOT / "config/base_camera_report.consolidated11.json").open(
                "r", encoding="utf-8") as handle:
            source = json.load(handle)
        with (ROOT / "config/base_camera_report.c525_reference1500.json").open(
                "r", encoding="utf-8") as handle:
            report = json.load(handle)
        with (ROOT / "config/arm_grasp_default.json").open(
                "r", encoding="utf-8") as handle:
            config = json.load(handle)
        expected = np.asarray(source["T_base_camera_reference"], dtype=float)
        rejected = rebase_base_camera_for_base_yaw(
            expected, report["rejected_delta_yaw_deg"]
        )
        self.assertTrue(np.allclose(expected, report["T_base_camera_reference"], atol=1e-12))
        self.assertTrue(np.allclose(
            expected,
            config["fixed_view_calibration"]["base_to_camera_matrix_4x4"],
            atol=1e-12,
        ))
        self.assertFalse(np.allclose(expected, rejected, atol=1e-6))
        self.assertEqual(
            config["fixed_view_calibration"]["reference_servo_pwms"],
            [1500, 1909, 1900, 620, 1500, 1500],
        )

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
            reference_servo_pwms=(1500, 1909, 1900, 620, 1500, 1500),
            base_to_camera_matrix_4x4=np.eye(4),
            rmse_m=0.001,
            max_error_m=0.002,
        )
        with self.assertRaisesRegex(ValueError, "calibrated is false"):
            validate_real_grasp_request(real_args(), real_config(), calibration)

    def test_calibration_error_thresholds_reject_real_grasp(self):
        calibration = FixedViewCalibration(
            calibrated=True,
            reference_servo_pwms=(1500, 1909, 1900, 620, 1500, 1500),
            base_to_camera_matrix_4x4=np.eye(4),
            rmse_m=0.011,
            max_error_m=0.016,
        )
        with self.assertRaisesRegex(ValueError, "rmse_m exceeds 0.010"):
            validate_real_grasp_request(real_args(), real_config(), calibration)

    def test_non_finite_calibration_limit_cannot_bypass_real_gate(self):
        calibration = FixedViewCalibration(
            calibrated=True,
            reference_servo_pwms=(1500, 1909, 1900, 620, 1500, 1500),
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
            reference_servo_pwms=(1500, 1909, 1900, 620, 1500, 1500),
            base_to_camera_matrix_4x4=np.eye(4),
            rmse_m=0.001,
            max_error_m=0.002,
        )
        config = real_config()
        config["kinematics"]["calibrated"] = False
        with self.assertRaisesRegex(ValueError, "kinematics.calibrated is false"):
            validate_real_grasp_request(real_args(), config, calibration)

    def test_unmeasured_joint_mapping_rejects_real_grasp(self):
        calibration = FixedViewCalibration(
            calibrated=True,
            reference_servo_pwms=(1500, 1909, 1900, 620, 1500, 1500),
            base_to_camera_matrix_4x4=np.eye(4),
            rmse_m=0.001,
            max_error_m=0.002,
        )
        config = real_config()
        config["joint_pwm_calibration"]["calibrated"] = False
        with self.assertRaisesRegex(
                ValueError, "joint_pwm_calibration.calibrated is false"):
            validate_real_grasp_request(real_args(), config, calibration)

    def test_max_stage_pre_grasp_plan_contains_no_approach(self):
        plan = build_fixed_view_grasp_plan(
            np.array([0.342, -0.014, 0.155], dtype=float),
            FakeKinematics(),
            GraspConfig(motion_settle_s=0.0),
            max_stage="PRE_GRASP",
        )
        self.assertEqual(
            [step.state for step in plan],
            [GraspState.OPEN, GraspState.PRE_GRASP],
        )
        self.assertNotIn(GraspState.APPROACH, [step.state for step in plan])

    def test_servo004_not_1500_rejects_real_grasp(self):
        reference = (1500, 1909, 1900, 620, 1490, 1500)
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
