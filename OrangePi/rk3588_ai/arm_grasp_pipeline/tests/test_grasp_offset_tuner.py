from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.tools import grasp_offset_tuner as tuner  # noqa: E402


class LiveGraspOffsetTunerTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(
            (ROOT / "config/arm_grasp_default.json").read_text(encoding="utf-8")
        )

    def test_parser_is_dry_run_and_pregrasp_by_default(self):
        args = tuner.parse_args([])
        self.assertTrue(args.dry_run)
        self.assertFalse(args.enable_arm)
        self.assertEqual(args.stage, "pregrasp")

    def test_only_pregrasp_or_final_align_are_accepted(self):
        self.assertEqual(tuner.parse_args(["--stage", "final_align"]).stage, "final_align")
        with self.assertRaises(SystemExit):
            tuner.parse_args(["--stage", "close"])

    def test_keyboard_edit_is_transactional_and_uses_mm(self):
        candidate = deepcopy(self.config)
        field = tuner.apply_live_key(candidate, ord("w"), 2.0)
        self.assertEqual(field, "along_mm")
        self.assertAlmostEqual(
            candidate["grasp_compensation"]["grasp_bias_approach_frame_m"][0],
            self.config["grasp_compensation"]["grasp_bias_approach_frame_m"][0]
            + 0.002,
        )
        tuner.config_tuner.apply_assignment(candidate, "pixel_y_ratio=0")
        before = deepcopy(candidate)
        with self.assertRaises(ValueError):
            tuner.apply_live_key(candidate, ord("["), 1.0)
        self.assertEqual(before, candidate)

    def test_enable_arm_is_rejected_before_live_hardware_setup(self):
        args = tuner.parse_args(["--enable_arm"])
        with self.assertRaisesRegex(ValueError, "observation-only"):
            tuner._run_live(
                args,
                ROOT / "config/arm_grasp_default.json",
                deepcopy(self.config),
            )

    def test_live_tuner_has_no_state_machine_motion_entrypoint(self):
        source = (ROOT / "tools/grasp_offset_tuner.py").read_text(encoding="utf-8")
        self.assertNotIn(".run_to_stage(", source)
        self.assertIn("allow_motion=False", source)
        self.assertIn("require_gripper_pwm=True", source)

    def test_unknown_key_is_noop(self):
        before = deepcopy(self.config)
        self.assertIsNone(tuner.apply_live_key(self.config, ord("?"), 1.0))
        self.assertEqual(before, self.config)

    def test_check_only_opens_no_hardware(self):
        self.assertEqual(
            tuner.main(
                [
                    "--config",
                    str(ROOT / "config/arm_grasp_default.json"),
                    "--check-only",
                ]
            ),
            0,
        )


if __name__ == "__main__":
    unittest.main()
