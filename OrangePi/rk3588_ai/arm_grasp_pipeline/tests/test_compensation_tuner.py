import ast
from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.tools import tune_grasp_compensation as tuner  # noqa: E402


class CompensationTunerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.config_path = self.directory / "arm_grasp.json"
        shutil.copy2(ROOT / "config/arm_grasp_default.json", self.config_path)
        self.original_bytes = self.config_path.read_bytes()

    def _run(self, *arguments):
        output = io.StringIO()
        args = tuner.parse_args(["--config", str(self.config_path), *arguments])
        with redirect_stdout(output):
            code = tuner.run(args)
        return code, output.getvalue()

    def _config(self):
        return json.loads(self.config_path.read_text(encoding="utf-8"))

    def test_module_has_no_hardware_facing_import(self):
        source = Path(tuner.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.append(node.module or "")
        forbidden_fragments = (
            "serial",
            "realsense",
            "arm_motion",
            "servo",
            "kinematics",
            "detector",
        )
        self.assertFalse(
            [
                name
                for name in imported
                if any(fragment in name.lower() for fragment in forbidden_fragments)
            ]
        )

    def test_check_only_is_default_and_never_modifies_config(self):
        code, output = self._run("--check-only")
        self.assertEqual(code, 0)
        self.assertEqual(self.config_path.read_bytes(), self.original_bytes)
        self.assertIn("CONFIGURATION_ONLY hardware_access=false", output)
        self.assertIn("ACTIVE_TCP CLOSED", output)
        self.assertIn("CHECK_ONLY config_not_modified=true", output)

    def test_read_only_preview_maps_physical_values_without_write(self):
        code, output = self._run(
            "--set",
            "along_mm=2",
            "--set",
            "lateral_mm=-3",
            "--set",
            "vertical_mm=1",
            "--set",
            "depth_bias_mm=-4",
            "--set",
            "object_radius_mm=35",
            "--set",
            "surface_to_center_mm=34",
            "--set",
            "final_insertion_mm=5",
        )
        self.assertEqual(code, 0)
        self.assertEqual(self.config_path.read_bytes(), self.original_bytes)
        self.assertIn(
            "along_mm,lateral_mm,vertical_mm,depth_bias_mm,object_radius_mm,surface_to_center_mm,final_insertion_mm",
            output,
        )
        self.assertIn("前后：沿末端接近轴", output)
        self.assertIn("左右：局部 approach 横向轴", output)
        self.assertIn("高低：局部 approach 竖直轴", output)
        self.assertIn("最终插入", output)

    def test_scripted_write_requires_exact_confirmation(self):
        args = tuner.parse_args(
            [
                "--config",
                str(self.config_path),
                "--set",
                "along_mm=1",
                "--write",
                "--confirm-save",
                "yes",
            ]
        )
        with redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError, "requires --confirm-save SAVE"):
                tuner.run(args)
        self.assertEqual(self.config_path.read_bytes(), self.original_bytes)
        self.assertEqual(list(self.directory.glob("*.bak.*")), [])

    def test_confirmed_write_creates_exact_backup_and_markdown_record(self):
        report = self.directory / "record.md"
        code, output = self._run(
            "--set",
            "along_mm=2",
            "--set",
            "lateral_mm=-1",
            "--set",
            "vertical_mm=3",
            "--set",
            "depth_bias_mm=-2",
            "--set",
            "object_radius_mm=35",
            "--set",
            "surface_to_center_mm=34",
            "--set",
            "final_insertion_mm=5",
            "--set",
            "pixel_y_ratio=0.6",
            "--write",
            "--confirm-save",
            "SAVE",
            "--report",
            str(report),
        )
        self.assertEqual(code, 0)
        backups = list(self.directory.glob("arm_grasp.json.bak.*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), self.original_bytes)

        config = self._config()
        compensation = config["grasp_compensation"]
        self.assertEqual(compensation["grasp_bias_approach_frame_m"], [0.002, -0.001, 0.003])
        self.assertEqual(compensation["depth_bias_m"], -0.002)
        self.assertEqual(compensation["object_surface_to_grasp_center_m"], 0.034)
        self.assertEqual(compensation["final_insertion_m"], 0.005)
        self.assertEqual(compensation["target_pixel_y_ratio"], 0.6)
        self.assertEqual(config["object_geometry"]["bottle_radius_m"], 0.035)

        text = report.read_text(encoding="utf-8")
        self.assertIn("# Grasp compensation tuning record", text)
        self.assertIn("Configuration saved: `true`", text)
        self.assertIn("Hardware access: `false`", text)
        self.assertIn("Active grasp TCP: `CLOSED", text)
        self.assertIn("`final_insertion_mm`", text)
        self.assertIn("surface_to_center_mm", text)
        self.assertIn("CONFIG_BACKUP", output)
        self.assertIn("REPORT_WRITTEN", output)

    def test_final_insertion_cannot_exceed_configured_limit(self):
        config = self._config()
        with self.assertRaisesRegex(ValueError, "max_final_insertion_m"):
            tuner.apply_assignment(config, "final_insertion_mm=16")

    def test_pixel_ratio_and_nonnegative_distances_are_validated(self):
        for assignment, expected in (
            ("pixel_y_ratio=1.1", "pixel_y_ratio"),
            ("surface_to_center_mm=-1", "surface_to_center_mm"),
            ("object_radius_mm=0", "object_radius_mm"),
            ("final_insertion_mm=-1", "final_insertion_mm"),
        ):
            config = self._config()
            with self.subTest(assignment=assignment):
                with self.assertRaisesRegex(ValueError, expected):
                    tuner.apply_assignment(config, assignment)

    def test_rejected_assignment_is_transactional_and_pixel_offsets_use_pixels(self):
        config = self._config()
        previous = tuner.display_value(config, "final_insertion_mm")
        with self.assertRaises(ValueError):
            tuner.apply_assignment(config, "final_insertion_mm=16")
        self.assertEqual(
            tuner.display_value(config, "final_insertion_mm"), previous
        )
        tuner.apply_assignment(config, "pixel_x_px=12")
        tuner.apply_assignment(config, "pixel_y_px=-8")
        self.assertEqual(tuner.display_value(config, "pixel_x_px"), 12.0)
        self.assertEqual(tuner.display_value(config, "pixel_y_px"), -8.0)

    def test_interactive_undo_and_reset_do_not_write(self):
        initial = self._config()
        with mock.patch("builtins.input", side_effect=["w", "undo", "d", "reset", "quit"]):
            with redirect_stdout(io.StringIO()):
                final, saved = tuner.interactive_session(
                    self.config_path, initial, step_mm=2.0
                )
        self.assertFalse(saved)
        self.assertEqual(tuner._changed_keys(initial, final), [])
        self.assertEqual(self.config_path.read_bytes(), self.original_bytes)

    def test_interactive_save_requires_save_token_and_can_sync_radius(self):
        initial = self._config()
        report = self.directory / "interactive.md"
        commands = ["y", "sync-radius", "save", "no", "save", "SAVE"]
        with mock.patch("builtins.input", side_effect=commands):
            with redirect_stdout(io.StringIO()):
                final, saved = tuner.interactive_session(
                    self.config_path,
                    deepcopy(initial),
                    step_mm=1.0,
                    report_path=report,
                )
        self.assertTrue(saved)
        self.assertEqual(tuner.display_value(final, "object_radius_mm"), 33.0)
        self.assertEqual(tuner.display_value(final, "surface_to_center_mm"), 33.0)
        self.assertTrue(report.is_file())
        self.assertNotEqual(self.config_path.read_bytes(), self.original_bytes)


if __name__ == "__main__":
    unittest.main()
