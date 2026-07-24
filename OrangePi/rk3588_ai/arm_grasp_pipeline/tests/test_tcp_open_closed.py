import json
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.geometry import FrameTransforms  # noqa: E402
from arm_grasp_pipeline.official_kinematics import OfficialArmKinematics  # noqa: E402


class OpenClosedTCPTests(unittest.TestCase):
    def setUp(self):
        config = json.loads(
            (ROOT / "config/arm_grasp_default.json").read_text(encoding="utf-8")
        )
        self.frames = FrameTransforms.from_config(config)
        self.kin = OfficialArmKinematics.from_config(
            config["kinematics"], config["joint_pwm_calibration"]
        )

    def test_open_and_closed_change_tcp_not_camera(self):
        pwm = (1500, 1909, 1900, 620)
        wrist = self.kin.forward_wrist_matrix_from_pwm(pwm)
        camera_before = self.frames.base_camera(wrist)
        opened = self.frames.base_tcp(wrist, "open")
        closed = self.frames.base_tcp(wrist, "closed")
        camera_after = self.frames.base_camera(wrist)
        self.assertTrue(np.array_equal(camera_before, camera_after))
        self.assertFalse(np.allclose(opened[:3, 3], closed[:3, 3]))
        self.assertAlmostEqual(
            float(np.linalg.norm(closed[:3, 3] - opened[:3, 3])), 0.019, places=9
        )

    def test_closed_tcp_uses_new_135_mm_measurement(self):
        self.assertTrue(self.frames.closed_calibrated)
        self.assertTrue(
            np.allclose(self.frames.T_wrist_tcp_closed[:3, 3], [0.135, 0.0, 0.0])
        )


if __name__ == "__main__":
    unittest.main()
