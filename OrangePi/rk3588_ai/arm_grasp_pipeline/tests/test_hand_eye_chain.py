import json
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.geometry import FrameTransforms, transform_point  # noqa: E402
from arm_grasp_pipeline.official_kinematics import OfficialArmKinematics  # noqa: E402


class HandEyeChainTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(
            (ROOT / "config/arm_grasp_default.json").read_text(encoding="utf-8")
        )
        self.frames = FrameTransforms.from_config(self.config)
        self.kin = OfficialArmKinematics.from_config(
            self.config["kinematics"], self.config["joint_pwm_calibration"]
        )

    def test_camera_chain_is_wrist_fk_times_fixed_hand_eye(self):
        pwm = (1520, 1850, 2020, 700)
        wrist = self.kin.forward_wrist_matrix_from_pwm(pwm)
        expected = wrist @ self.frames.T_wrist_camera
        actual = self.frames.base_camera(wrist)
        self.assertTrue(np.allclose(actual, expected, atol=1e-12))

    def test_column_vector_transform_direction(self):
        wrist = self.kin.forward_wrist_matrix_from_pwm((1500, 1909, 1900, 620))
        camera = self.frames.base_camera(wrist)
        point_camera = np.array([0.01, -0.02, 0.30])
        direct = (camera @ np.array([0.01, -0.02, 0.30, 1.0]))[:3]
        self.assertTrue(np.allclose(transform_point(camera, point_camera), direct))


if __name__ == "__main__":
    unittest.main()
