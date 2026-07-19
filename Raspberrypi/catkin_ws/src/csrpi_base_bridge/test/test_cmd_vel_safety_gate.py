#!/usr/bin/env python3

import importlib.util
from pathlib import Path
import unittest

from geometry_msgs.msg import Twist


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "cmd_vel_safety_gate.py"
)
SPEC = importlib.util.spec_from_file_location("cmd_vel_safety_gate", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CmdVelSafetyGateLimitTest(unittest.TestCase):
    def make_gate(
        self,
        min_vx=0.0,
        max_vx=0.20,
        max_vy=0.15,
        max_wz=0.5,
        allow_lateral=True,
    ):
        gate = MODULE.CmdVelSafetyGate.__new__(MODULE.CmdVelSafetyGate)
        gate.min_vx = min_vx
        gate.max_vx = max_vx
        gate.max_vy = max_vy
        gate.max_wz = max_wz
        gate.allow_lateral = allow_lateral
        return gate

    def test_default_policy_blocks_reverse_and_preserves_lateral_motion(self):
        source = Twist()
        source.linear.x = -0.10
        source.linear.y = 0.08
        source.angular.z = 0.30

        limited = self.make_gate().apply_limits(source)

        self.assertEqual(limited.linear.x, 0.0)
        self.assertAlmostEqual(limited.linear.y, 0.08)
        self.assertAlmostEqual(limited.angular.z, 0.30)

    def test_forward_and_rotation_limits_still_apply(self):
        source = Twist()
        source.linear.x = 0.35
        source.angular.z = -0.80

        limited = self.make_gate().apply_limits(source)

        self.assertAlmostEqual(limited.linear.x, 0.20)
        self.assertAlmostEqual(limited.angular.z, -0.50)

    def test_explicit_override_can_restore_supervised_reverse(self):
        source = Twist()
        source.linear.x = -0.10
        source.linear.y = -0.08

        limited = self.make_gate(min_vx=-0.20).apply_limits(source)

        self.assertAlmostEqual(limited.linear.x, -0.10)
        self.assertAlmostEqual(limited.linear.y, -0.08)

    def test_lateral_motion_can_be_explicitly_disabled(self):
        source = Twist()
        source.linear.y = 0.08

        limited = self.make_gate(allow_lateral=False).apply_limits(source)

        self.assertEqual(limited.linear.y, 0.0)


if __name__ == "__main__":
    unittest.main()
