import json
from dataclasses import replace
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.bottle_demo import (
    BottleDemoConfig,
    BottleDemoStop,
    BottleDemoVision,
    RGBIdentityGuard,
    bounded_horizontal_step,
    full_hold_assignments,
)
from arm_grasp_pipeline.target_depth import BBox
from arm_grasp_pipeline.geometry import FrameTransforms
from arm_grasp_pipeline.grasp_planner import GraspConfig, plan_final_insertion, plan_pregrasp
from arm_grasp_pipeline.official_kinematics import OfficialArmKinematics


class BottleDemoTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(
            (ROOT / "config/arm_grasp_default.json").read_text(encoding="utf-8")
        )

    def test_physical_demo_config_and_height_offset_are_consistent(self):
        demo = BottleDemoConfig.from_mapping(self.config["demo_grasp"])
        self.assertEqual((1500, 1909, 1968, 620, 1500, 1112), demo.prepare_pose_pwms)
        self.assertEqual(0.008, demo.near_approach_step_m)
        self.assertEqual(0.04, demo.grasp_height_offset_m)
        self.assertEqual(
            demo.grasp_height_offset_m,
            self.config["grasp_compensation"]["grasp_height_offset_m"],
        )
        previous = demo.observable_pregrasp_standoff_m
        for standoff, pitch in demo.approach_profile_standoff_pitch:
            self.assertAlmostEqual(0.008, previous - standoff, places=9)
            if standoff <= demo.horizontal_only_from_standoff_m:
                self.assertEqual(0.0, pitch)
            previous = standoff
        self.assertAlmostEqual(demo.near_close_distance_m, previous, places=9)

    def test_full_hold_assignment_always_contains_all_six_and_locks_wrist(self):
        assignments = full_hold_assignments(
            (1500, 1909, 1968, 620, 1500, 1112), {0: 1470, 3: 650}
        )
        self.assertEqual(set(range(6)), set(assignments))
        self.assertEqual(1500, assignments[4])
        self.assertEqual(1112, assignments[5])
        self.assertEqual(1470, assignments[0])

    def test_horizontal_step_is_bounded_to_eight_mm(self):
        self.assertEqual(0.008, bounded_horizontal_step(0.06, 0.008, 0.005, 0.005))
        self.assertEqual(0.0, bounded_horizontal_step(0.004, 0.008, 0.005, 0.005))
        with self.assertRaises(BottleDemoStop):
            bounded_horizontal_step(0.006, 0.004, 0.005, 0.001)

    def test_near_identity_guard_allows_bottle_to_cup_alias(self):
        first = BBox(250, 100, 390, 420, 0.91, "bottle")
        second = BBox(245, 95, 400, 430, 0.88, "cup")
        guard = RGBIdentityGuard(("bottle", "cup"), 120.0, 2.2, first)
        self.assertEqual(second, guard.associate((second,), 0.25))

    def test_transparent_bottle_depth_samples_configured_cap_region(self):
        demo = BottleDemoConfig.from_mapping(self.config["demo_grasp"])
        vision = BottleDemoVision(None, None, self.config, demo, 0.25)
        bbox = BBox(200, 100, 400, 400, 0.9, "bottle")
        self.assertEqual((300.0, 142.0), vision._depth_sample_pixel(bbox))

    def test_near_identity_guard_stops_on_jump_or_ambiguity(self):
        first = BBox(250, 100, 390, 420, 0.91, "bottle")
        jumped = BBox(10, 10, 100, 200, 0.90, "bottle")
        guard = RGBIdentityGuard(("bottle", "cup"), 80.0, 2.2, first)
        with self.assertRaises(BottleDemoStop):
            guard.associate((jumped,), 0.25)

        guard = RGBIdentityGuard(("bottle", "cup"), 120.0, 2.2, first)
        a = BBox(245, 100, 390, 420, 0.90, "bottle")
        b = BBox(255, 105, 400, 425, 0.89, "cup")
        with self.assertRaises(BottleDemoStop):
            guard.associate((a, b), 0.25)

    def test_measured_demo_example_has_safe_eight_mm_profile(self):
        demo = BottleDemoConfig.from_mapping(self.config["demo_grasp"])
        frames = FrameTransforms.from_config(self.config)
        kin = OfficialArmKinematics.from_config(
            self.config["kinematics"], self.config["joint_pwm_calibration"]
        )
        grasp = GraspConfig.from_mapping(self.config["grasp"])
        pwms = tuple(demo.prepare_pose_pwms)
        current = frames.base_tcp(
            kin.forward_wrist_matrix_from_pwm(pwms[:4]), "closed"
        )
        # Latest hardware-free replay of the transparent-bottle cap depth
        # lock (0.310--0.311 m) after the +40 mm grasp-height compensation.
        target = np.array((0.3341, 0.0056, 0.1031), dtype=float)
        axis = target.copy()
        axis[2] = 0.0
        axis /= np.linalg.norm(axis)
        observation = plan_pregrasp(
            current,
            target,
            axis,
            frames.T_wrist_tcp_closed,
            kin,
            replace(grasp, pregrasp_pitch_deg=demo.observable_pregrasp_pitch_deg),
            pwms,
            demo.observable_pregrasp_standoff_m,
        )
        current = observation.target_T_base_tcp
        pwms = observation.servo_pwms
        for standoff, pitch in demo.approach_profile_standoff_pitch:
            step = plan_pregrasp(
                current,
                target,
                axis,
                frames.T_wrist_tcp_closed,
                kin,
                replace(grasp, pregrasp_pitch_deg=pitch),
                pwms,
                standoff,
            )
            self.assertAlmostEqual(0.008, np.linalg.norm(step.step_xyz_m), places=7)
            self.assertLessEqual(
                max(abs(step.servo_pwms[index] - pwms[index]) for index in range(4)),
                self.config["closed_loop"]["max_joint_pwm_step"],
            )
            current = step.target_T_base_tcp
            pwms = step.servo_pwms
        final = plan_final_insertion(
            current,
            axis,
            demo.final_horizontal_insertion_m,
            demo.final_horizontal_insertion_m,
            frames.T_wrist_tcp_closed,
            kin,
            grasp,
            pwms,
            horizontal_only=True,
        )
        self.assertIsNotNone(final)
        self.assertAlmostEqual(0.006, np.linalg.norm(final.step_xyz_m), places=7)
        self.assertAlmostEqual(0.0, final.xyz_m[2] - current[2, 3], places=9)


if __name__ == "__main__":
    unittest.main()
