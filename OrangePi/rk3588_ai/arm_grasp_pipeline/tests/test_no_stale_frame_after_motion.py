from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.grasp_state_machine import DynamicGraspStateMachine  # noqa: E402
from arm_grasp_pipeline.tests.dynamic_fakes import (  # noqa: E402
    StaticTargetSource,
    runtime_parts,
)


class FreshFrameTests(unittest.TestCase):
    def test_each_motion_is_followed_by_a_later_frame(self):
        config, frames, kin, adapter, arm, target = runtime_parts()
        source = StaticTargetSource(adapter, kin, frames, target)
        machine = DynamicGraspStateMachine(arm, frames, config, allow_motion=True)
        outcome = machine.run_to_stage(source, "approach")
        self.assertTrue(outcome.ok, outcome.reason)
        motions = [
            row for row in machine.logger.records if "motion_end_monotonic" in row
        ]
        self.assertGreaterEqual(len(source.calls), len(motions) + 1)
        for motion in motions:
            later = [
                call
                for call in source.calls
                if call["after"] >= motion["motion_end_monotonic"]
            ]
            self.assertTrue(later, motion)
            self.assertGreater(
                later[0]["acquired"], motion["motion_end_monotonic"]
            )

    def test_stale_frame_is_fail_closed_without_motion(self):
        config, frames, kin, adapter, arm, target = runtime_parts()
        source = StaticTargetSource(adapter, kin, frames, target, stale_call=1)
        machine = DynamicGraspStateMachine(arm, frames, config, allow_motion=True)
        outcome = machine.run_to_stage(source, "pregrasp")
        self.assertFalse(outcome.ok)
        self.assertIn("stale RGB-D frame", outcome.reason)
        self.assertEqual(outcome.commands_executed, 0)
        self.assertEqual(adapter.read_required_pwms().ordered(), tuple(config["serial"]["initial_dry_run_pwms"]))


if __name__ == "__main__":
    unittest.main()
