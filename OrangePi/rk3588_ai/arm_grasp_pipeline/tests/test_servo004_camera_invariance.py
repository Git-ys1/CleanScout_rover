import json
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.geometry import (  # noqa: E402
    FrameTransforms,
    dynamic_base_camera_from_pwm,
)
from arm_grasp_pipeline.official_kinematics import OfficialArmKinematics  # noqa: E402


class Servo004CameraInvarianceTests(unittest.TestCase):
    def test_servo004_and_servo005_are_absent_from_camera_chain(self):
        config = json.loads(
            (ROOT / "config/arm_grasp_default.json").read_text(encoding="utf-8")
        )
        frames = FrameTransforms.from_config(config)
        kin = OfficialArmKinematics.from_config(
            config["kinematics"], config["joint_pwm_calibration"]
        )
        upstream = [1500, 1909, 1900, 620]
        first = dynamic_base_camera_from_pwm(kin, upstream + [1500, 1000], frames)
        second = dynamic_base_camera_from_pwm(kin, upstream + [1800, 2200], frames)
        self.assertTrue(np.array_equal(first, second))


if __name__ == "__main__":
    unittest.main()
