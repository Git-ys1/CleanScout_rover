from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.tools import bottle_grasp_demo  # noqa: E402


class StrictStageEntrypointTests(unittest.TestCase):
    def test_stage_script_uses_only_strict_dynamic_runtime(self):
        text = (ROOT / "tools/run_bottle_stage.sh").read_text(encoding="utf-8")
        self.assertIn("tools/d435_yolo_grasp.py", text)
        self.assertNotIn("tools/bottle_grasp_demo.py", text)
        self.assertNotIn("allow_missing_gripper_prad", text)
        self.assertNotIn("resume_lock", text)
        for stage in ("observe", "center", "pregrasp", "approach", "close", "lift"):
            self.assertIn(stage, text)

    def test_legacy_bottle_demo_real_mode_fails_before_hardware_import(self):
        with self.assertRaisesRegex(ValueError, "real motion is retired"):
            bottle_grasp_demo.main(
                ["--dry_run", "false", "--enable_arm", "--max_stage", "approach"]
            )


if __name__ == "__main__":
    unittest.main()
