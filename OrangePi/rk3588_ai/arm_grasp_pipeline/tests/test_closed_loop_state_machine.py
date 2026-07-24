from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.grasp_state_machine import (  # noqa: E402
    DynamicGraspStateMachine,
    GraspState,
)
from arm_grasp_pipeline.tests.dynamic_fakes import (  # noqa: E402
    StaticTargetSource,
    runtime_parts,
)


class ClosedLoopStateMachineTests(unittest.TestCase):
    def make_machine(self, **source_kwargs):
        config, frames, kin, adapter, arm, target = runtime_parts()
        source = StaticTargetSource(adapter, kin, frames, target, **source_kwargs)
        machine = DynamicGraspStateMachine(
            arm, frames, config, allow_motion=True
        )
        return machine, source, adapter

    def test_pregrasp_reacquires_but_never_approaches(self):
        machine, source, adapter = self.make_machine()
        outcome = machine.run_to_stage(source, "pregrasp")
        self.assertTrue(outcome.ok, outcome.reason)
        self.assertEqual(outcome.state, GraspState.DONE)
        self.assertEqual(outcome.commands_executed, 2)  # OPEN + PREGRASP
        labels = [
            row.get("motion_label")
            for row in machine.logger.records
            if row.get("motion_label")
        ]
        self.assertEqual(labels, ["OPEN", "MOVE_PREGRASP"])
        self.assertGreaterEqual(len(source.calls), 3)
        self.assertIsNone(adapter._ser)
        contexts = [
            row
            for row in machine.logger.records
            if row.get("state") == "DEPTH_LOCK" and "raw_point_camera" in row
        ]
        self.assertTrue(contexts)
        for key in (
            "raw_pixel",
            "raw_depth",
            "object_center_point",
            "local_approach_frame",
            "final_grasp_point_base",
            "applied_compensation",
        ):
            self.assertIn(key, contexts[-1])

    def test_approach_is_replanned_in_5_to_10_mm_steps(self):
        machine, source, adapter = self.make_machine()
        outcome = machine.run_to_stage(source, "approach")
        self.assertTrue(outcome.ok, outcome.reason)
        self.assertGreater(outcome.approach_iterations, 1)
        planned = [
            row
            for row in machine.logger.records
            if row.get("state") == "FINE_APPROACH" and "planned_step_xyz" in row
        ]
        self.assertEqual(len(planned), outcome.approach_iterations)
        for row in planned:
            length = float(np.linalg.norm(row["planned_step_xyz"]))
            self.assertGreaterEqual(length, 0.005 - 1e-12)
            self.assertLessEqual(length, 0.010 + 1e-12)
        self.assertEqual(
            adapter.read_required_pwms().pwms[5],
            machine.grasp_cfg.gripper_open_pwm,
        )
        self.assertFalse(any("P2000" in row.get("command", "") for row in machine.logger.records))

    def test_target_loss_after_pregrasp_stops_before_approach(self):
        machine, source, _ = self.make_machine(fail_call=4)
        outcome = machine.run_to_stage(source, "approach")
        self.assertFalse(outcome.ok)
        self.assertIn("target lost", outcome.reason)
        self.assertEqual(outcome.commands_executed, 2)
        self.assertEqual(outcome.approach_iterations, 0)

    def test_track_switch_after_pregrasp_stops_before_approach(self):
        machine, source, _ = self.make_machine(switch_call=4)
        outcome = machine.run_to_stage(source, "approach")
        self.assertFalse(outcome.ok)
        self.assertIn("track switched", outcome.reason)
        self.assertEqual(outcome.commands_executed, 2)

    def test_close_stage_performs_small_verification_but_not_full_lift(self):
        machine, source, adapter = self.make_machine(attach_on_close=True)
        outcome = machine.run_to_stage(source, "close")
        self.assertTrue(outcome.ok, outcome.reason)
        self.assertEqual(outcome.grasp_verification, "grasp_verified")
        self.assertEqual(adapter.read_required_pwms().pwms[5], 2000)
        labels = [
            row.get("motion_label")
            for row in machine.logger.records
            if row.get("motion_label")
        ]
        self.assertIn("CLOSE", labels)
        self.assertIn("VERIFY_LIFT", labels)
        self.assertNotIn("LIFT", labels)

    def test_attached_object_is_verified_before_full_lift(self):
        machine, source, adapter = self.make_machine(attach_on_close=True)
        outcome = machine.run_to_stage(source, "lift")
        self.assertTrue(outcome.ok, outcome.reason)
        self.assertEqual(outcome.grasp_verification, "grasp_verified")
        labels = [
            row.get("motion_label")
            for row in machine.logger.records
            if row.get("motion_label")
        ]
        self.assertLess(labels.index("VERIFY_LIFT"), labels.index("LIFT"))
        self.assertEqual(adapter.read_required_pwms().pwms[5], 2000)

    def test_table_static_object_fails_verification_and_blocks_full_lift(self):
        machine, source, _ = self.make_machine(attach_on_close=False)
        outcome = machine.run_to_stage(source, "lift")
        self.assertFalse(outcome.ok)
        self.assertEqual(outcome.grasp_verification, "grasp_failed")
        labels = [
            row.get("motion_label")
            for row in machine.logger.records
            if row.get("motion_label")
        ]
        self.assertIn("VERIFY_LIFT", labels)
        self.assertNotIn("LIFT", labels)

    def test_final_insertion_is_horizontal_only_then_close(self):
        machine, source, _ = self.make_machine(attach_on_close=True)
        outcome = machine.run_to_stage(source, "close")
        self.assertTrue(outcome.ok, outcome.reason)
        insertions = [
            row
            for row in machine.logger.records
            if row.get("state") == "FINAL_ALIGN" and "planned_step_xyz" in row
        ]
        self.assertEqual(len(insertions), 1)
        step = insertions[0]["planned_step_xyz"]
        self.assertAlmostEqual(step[2], 0.0, places=12)
        self.assertAlmostEqual(float(np.linalg.norm(step)), 0.010, places=6)

    def test_depth_below_measured_17_cm_floor_stops_before_motion(self):
        machine, source, _ = self.make_machine(depth_override_m=0.16)
        outcome = machine.run_to_stage(source, "pregrasp")
        self.assertFalse(outcome.ok)
        self.assertIn("unreliable zone", outcome.reason)
        self.assertEqual(outcome.commands_executed, 0)

    def test_real_close_requires_accepted_gripper_endpoint_measurement(self):
        machine, _, _ = self.make_machine()
        machine.arm.adapter.dry_run = False
        with self.assertRaisesRegex(ValueError, "safe close/contact"):
            machine.require_real_close_calibration()
        machine.config["grasp"]["gripper_close_calibrated"] = True
        machine.require_real_close_calibration()


if __name__ == "__main__":
    unittest.main()
