import json
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.geometry import FrameTransforms  # noqa: E402
from arm_grasp_pipeline.official_kinematics import OfficialArmKinematics  # noqa: E402


class WristFKTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(
            (ROOT / "config/arm_grasp_default.json").read_text(encoding="utf-8")
        )
        cls.kin = OfficialArmKinematics.from_config(
            cls.config["kinematics"], cls.config["joint_pwm_calibration"]
        )
        cls.frames = FrameTransforms.from_config(cls.config)

    def test_fk_repeated_100_times_has_no_drift(self):
        pwm = (1500, 1909, 1900, 620)
        expected = self.kin.forward_wrist_matrix_from_pwm(pwm)
        for _ in range(100):
            actual = self.kin.forward_wrist_matrix_from_pwm(pwm)
            self.assertTrue(np.array_equal(actual, expected))

    def test_each_upstream_servo_changes_wrist(self):
        base = (1500, 1900, 1900, 800)
        expected = self.kin.forward_wrist_matrix_from_pwm(base)
        for index in range(4):
            changed = list(base)
            changed[index] += 20
            actual = self.kin.forward_wrist_matrix_from_pwm(changed)
            self.assertFalse(np.allclose(actual, expected, atol=1e-12), index)

    def test_frozen_zero_sign_and_slopes(self):
        cfg = self.config["joint_pwm_calibration"]
        self.assertEqual(cfg["zero_pwms"], [1500, 1500, 1500, 1500])
        self.assertEqual(cfg["pwm_signs"], [1, -1, 1, 1])
        self.assertEqual(
            cfg["pwm_per_deg_by_joint"],
            [
                8.148148148148149,
                7.0908242948362,
                7.93582743625423,
                6.478095739111546,
            ],
        )
        self.assertEqual(self.kin.pwm_to_joint_angles_deg((1500,) * 4), (0.0,) * 4)
        angles = self.kin.pwm_to_joint_angles_deg((1510, 1510, 1510, 1510))
        self.assertGreater(angles[0], 0.0)
        self.assertLess(angles[1], 0.0)
        self.assertGreater(angles[2], 0.0)
        self.assertGreater(angles[3], 0.0)

    def test_tcp_ik_fk_round_trip(self):
        source_pwm = (1481, 1129, 1977, 1646)
        target = self.kin.forward_tcp_matrix_from_pwm(
            source_pwm, self.frames.T_wrist_tcp_closed
        )
        result = self.kin.inverse_tcp_pose(
            target_T_base_tcp=target,
            T_wrist_tcp=self.frames.T_wrist_tcp_closed,
        )
        self.assertIsNotNone(result)
        self.assertLess(
            float(np.linalg.norm(result.tcp_matrix[:3, 3] - target[:3, 3])),
            0.001,
        )
        limits = self.config["grasp"]["servo_pwm_limits"][:4]
        for value, bounds in zip(result.servo_pwms, limits):
            self.assertGreaterEqual(value, bounds[0])
            self.assertLessEqual(value, bounds[1])


if __name__ == "__main__":
    unittest.main()
