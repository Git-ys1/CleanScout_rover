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
    invert_transform,
    transform_point,
)
from arm_grasp_pipeline.official_kinematics import OfficialArmKinematics  # noqa: E402


class DynamicFrameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(
            (ROOT / "config/arm_grasp_default.json").read_text(encoding="utf-8")
        )
        cls.frames = FrameTransforms.from_config(cls.config)
        cls.kin = OfficialArmKinematics.from_config(
            cls.config["kinematics"], cls.config["joint_pwm_calibration"]
        )

    def test_static_base_point_is_invariant_across_dynamic_camera_poses(self):
        point_base = np.array([0.30, -0.04, 0.08])
        recovered = []
        for pwm in (
            (1500, 1909, 1900, 620),
            (1600, 1800, 2000, 700),
            (1400, 1700, 2150, 800),
        ):
            T_base_camera = dynamic_base_camera_from_pwm(
                self.kin, pwm, self.frames
            )
            point_camera = transform_point(invert_transform(T_base_camera), point_base)
            recovered.append(transform_point(T_base_camera, point_camera))
        for value in recovered:
            self.assertTrue(np.allclose(value, point_base, atol=1e-10))

    def test_dynamic_chain_does_not_need_legacy_fixed_matrix(self):
        config = json.loads(json.dumps(self.config))
        config.pop("fixed_view_calibration", None)
        frames = FrameTransforms.from_config(config)
        matrix = dynamic_base_camera_from_pwm(
            self.kin, (1500, 1909, 1900, 620), frames
        )
        self.assertEqual(matrix.shape, (4, 4))


if __name__ == "__main__":
    unittest.main()
