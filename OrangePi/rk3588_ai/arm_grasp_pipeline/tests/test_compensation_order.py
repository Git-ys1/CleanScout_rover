import json
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.geometry import (  # noqa: E402
    EnvironmentGeometry,
    apply_grasp_compensation,
    apply_target_pixel_offset,
)


class CompensationOrderTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(
            (ROOT / "config/arm_grasp_default.json").read_text(encoding="utf-8")
        )

    def test_physical_order_and_intermediate_values_are_reproducible(self):
        compensation = dict(self.config["grasp_compensation"])
        compensation.update(
            {
                "target_pixel_offset_px": [3.0, -4.0],
                "depth_bias_m": 0.1,
                "camera_point_bias_m": [0.01, -0.02, 0.03],
                "object_surface_to_grasp_center_m": 0.032,
                "object_center_axis": "camera_ray",
                "grasp_bias_approach_frame_m": [0.002, -0.003, 0.004],
                "grasp_height_offset_m": 0.005,
                "final_insertion_m": 0.006,
            }
        )
        raw = np.array([0.1, 0.2, 1.0])
        result = apply_grasp_compensation(raw, np.eye(4), compensation)
        # Depth bias scales the complete ray before the camera XYZ bias.
        expected_corrected = np.array([0.11, 0.22, 1.10]) + np.array([0.01, -0.02, 0.03])
        self.assertTrue(np.allclose(result.corrected_point_camera, expected_corrected))
        self.assertTrue(np.allclose(result.raw_point_base_surface, expected_corrected))
        ray = expected_corrected / np.linalg.norm(expected_corrected)
        expected_center = expected_corrected + ray * 0.032
        self.assertTrue(np.allclose(result.object_center_point, expected_center))
        local = result.local_approach_frame[:3, :3]
        expected_final = expected_center + local @ np.array([0.008, -0.003, 0.009])
        self.assertTrue(np.allclose(result.final_grasp_point_base, expected_final))
        self.assertEqual(apply_target_pixel_offset((10, 20), (3, -4)), (13.0, 16.0))

    def test_final_insertion_is_an_explicit_last_along_axis_term(self):
        first = dict(self.config["grasp_compensation"])
        first["final_insertion_m"] = 0.0
        second = dict(first)
        second["final_insertion_m"] = 0.01
        # The configured physical motion axis is horizontal-radial in base.
        # Use a non-degenerate reachable surface point instead of a point
        # exactly above the base axis, where that axis is intentionally
        # undefined.
        no_insert = apply_grasp_compensation((0.2, 0.0, 0.5), np.eye(4), first)
        inserted = apply_grasp_compensation((0.2, 0.0, 0.5), np.eye(4), second)
        delta = np.asarray(inserted.final_grasp_point_base) - np.asarray(
            no_insert.final_grasp_point_base
        )
        self.assertTrue(
            np.allclose(delta, inserted.local_approach_frame[:3, 0] * 0.01)
        )

    def test_table_height_uses_new_120_mm_measurement(self):
        environment = EnvironmentGeometry.from_config(self.config)
        self.assertAlmostEqual(environment.base_mounting_plane_to_table_m, 0.120)
        self.assertAlmostEqual(environment.table_surface_z_base_m, -0.120)


if __name__ == "__main__":
    unittest.main()
