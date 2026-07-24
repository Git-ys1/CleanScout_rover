import json
from pathlib import Path
import re
import sys
import unittest
from unittest import mock

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.arm_motion import ArmMotion, MotionSafetyError  # noqa: E402
from arm_grasp_pipeline.geometry import FrameTransforms  # noqa: E402
from arm_grasp_pipeline.official_kinematics import OfficialArmKinematics  # noqa: E402
from arm_grasp_pipeline.serial_servo_adapter import (  # noqa: E402
    PWMReadbackError,
    SerialServoArmAdapter,
)


class FakeSerial:
    MOVE_RE = re.compile(rb"#(?P<id>\d{3})P(?P<pwm>\d{4})T\d{4}!")
    READ_RE = re.compile(rb"#(?P<id>\d{3})PRAD!")

    def __init__(self, positions=None, short_write=False, omit_ids=()):
        self.positions = dict(
            positions or {0: 1500, 1: 1909, 2: 1900, 3: 620, 4: 1500, 5: 1000}
        )
        self.short_write = bool(short_write)
        self.omit_ids = set(int(value) for value in omit_ids)
        self.writes = []
        self._rx = bytearray()

    @property
    def in_waiting(self):
        return len(self._rx)

    def write(self, payload):
        payload = bytes(payload)
        self.writes.append(payload)
        if self.short_write:
            return max(0, len(payload) - 1)
        for match in self.MOVE_RE.finditer(payload):
            self.positions[int(match.group("id"))] = int(match.group("pwm"))
        read = self.READ_RE.fullmatch(payload)
        if read:
            servo_id = int(read.group("id"))
            if servo_id not in self.omit_ids:
                self._rx.extend(
                    "#{:03d}P{:04d}!".format(
                        servo_id, self.positions[servo_id]
                    ).encode("ascii")
                )
        return len(payload)

    def flush(self):
        return None

    def reset_input_buffer(self):
        self._rx.clear()

    def read(self, size):
        value = bytes(self._rx[:size])
        del self._rx[:size]
        return value

    def close(self):
        return None


def real_adapter(fake):
    adapter = SerialServoArmAdapter(
        dry_run=False,
        readback_timeout_s=0.01,
        motion_settle_s=0.0,
    )
    adapter._ser = fake
    adapter._read_response_locked = (
        lambda timeout_s=0.8, idle_s=0.08: fake.read(fake.in_waiting)
    )
    return adapter


class SerialReadbackTests(unittest.TestCase):
    def test_real_success_requires_exact_write_and_fresh_prad(self):
        fake = FakeSerial()
        adapter = real_adapter(fake)
        with mock.patch("arm_grasp_pipeline.serial_servo_adapter.time.sleep"):
            result = adapter.send_and_wait_readback(
                {0: 1510, 4: 1500}, 20, settle_s=0.0
            )
        self.assertTrue(result.ok)
        self.assertTrue(result.command_written)
        self.assertTrue(result.readback_reached)
        self.assertFalse(result.simulated)
        self.assertEqual(result.snapshot.pwms[0], 1510)
        self.assertEqual(set(result.snapshot.pwms), set(range(6)))
        self.assertFalse(any(b"PDST" in item for item in fake.writes))

    def test_short_write_is_not_completion(self):
        fake = FakeSerial(short_write=True)
        adapter = real_adapter(fake)
        result = adapter.send_and_wait_readback({0: 1510}, 20, settle_s=0.0)
        self.assertFalse(result.ok)
        self.assertFalse(result.command_written)
        self.assertIn("short write", result.reason)

    def test_missing_prad_id_fails(self):
        fake = FakeSerial(omit_ids={5})
        adapter = real_adapter(fake)
        with mock.patch("arm_grasp_pipeline.serial_servo_adapter.time.sleep"):
            result = adapter.send_and_wait_readback(
                {0: 1510}, 20, settle_s=0.0, retries=2
            )
        self.assertFalse(result.ok)
        self.assertIn("missing required servo IDs", result.reason)
        self.assertIsNotNone(result.snapshot)
        self.assertNotIn(5, result.snapshot.pwms)

    def test_retry_snapshots_are_never_stitched(self):
        adapter = SerialServoArmAdapter(dry_run=False, readback_retries=2)
        calls = {servo_id: 0 for servo_id in range(6)}

        def alternating_read(servo_id, timeout_s=0.8):
            attempt = calls[servo_id]
            calls[servo_id] += 1
            if (attempt == 0 and servo_id == 5) or (attempt == 1 and servo_id == 0):
                return None
            return 1500

        adapter.read_pwm = alternating_read
        with self.assertRaises(PWMReadbackError):
            adapter.read_required_pwms(range(6), retries=2)

    def test_invalid_read_gate_is_rejected_before_write(self):
        fake = FakeSerial()
        adapter = real_adapter(fake)
        with self.assertRaises(ValueError):
            adapter.send_and_wait_readback({0: 1510}, 20, required_ids=())
        self.assertEqual(fake.writes, [])

    def test_servo004_is_a_command_and_snapshot_gate(self):
        adapter = SerialServoArmAdapter(dry_run=True)
        with self.assertRaises(ValueError):
            adapter.send_and_wait_readback({4: 1499}, 20)

        unsafe = SerialServoArmAdapter(
            dry_run=True,
            initial_pwms=[1500, 1500, 1500, 1500, 1400, 1500],
        )
        result = unsafe.send_and_wait_readback({0: 1510}, 20)
        self.assertFalse(result.ok)
        self.assertIn(4, result.mismatches)

    def test_dry_run_is_explicitly_simulated(self):
        adapter = SerialServoArmAdapter(dry_run=True)
        result = adapter.send_and_wait_readback({0: 1510, 4: 1500}, 20)
        self.assertTrue(result.ok)
        self.assertTrue(result.simulated)
        self.assertFalse(result.command_written)
        self.assertTrue(result.snapshot.simulated)


class ArmMotionReadbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(
            (ROOT / "config/arm_grasp_default.json").read_text(encoding="utf-8")
        )
        cls.kin = OfficialArmKinematics.from_config(
            cls.config["kinematics"], cls.config["joint_pwm_calibration"]
        )
        cls.frames = FrameTransforms.from_config(cls.config)

    def test_actual_pose_is_derived_from_snapshot(self):
        initial = [1500, 1909, 1900, 620, 1500, 1000]
        motion = ArmMotion(
            SerialServoArmAdapter(dry_run=True, initial_pwms=initial),
            self.kin,
        )
        actual = motion.get_actual_tcp_pose(
            self.frames.T_wrist_tcp_closed, tcp_name="closed"
        )
        expected = self.kin.forward_tcp_matrix_from_pwm(
            initial[:4], self.frames.T_wrist_tcp_closed
        )
        self.assertTrue(np.allclose(actual.matrix, expected, atol=1e-12))
        self.assertTrue(actual.snapshot.simulated)

    def test_motion_success_contains_readback_evidence(self):
        adapter = SerialServoArmAdapter(
            dry_run=True,
            initial_pwms=[1500, 1909, 1900, 620, 1500, 1000],
        )
        motion = ArmMotion(adapter, self.kin)
        target = self.kin.forward_tcp_matrix_from_pwm(
            (1481, 1129, 1977, 1646), self.frames.T_wrist_tcp_closed
        )
        ik = self.kin.inverse_tcp_pose(
            target_T_base_tcp=target,
            T_wrist_tcp=self.frames.T_wrist_tcp_closed,
        )
        result = motion.execute_ik(ik, 20)
        self.assertTrue(result.ok)
        self.assertTrue(result.readback_reached)
        self.assertTrue(result.simulated)
        self.assertEqual(result.readback_snapshot.pwms[4], 1500)

    def test_measured_servo004_violation_stops_pose_use(self):
        adapter = SerialServoArmAdapter(
            dry_run=True,
            initial_pwms=[1500, 1909, 1900, 620, 1499, 1000],
            fixed_pwm_requirements={},
        )
        motion = ArmMotion(adapter, self.kin)
        with self.assertRaises(MotionSafetyError):
            motion.get_actual_pwm_snapshot()

    def test_read_only_wrist_observation_does_not_require_gripper_prad(self):
        fake = FakeSerial(omit_ids={5})
        adapter = real_adapter(fake)
        motion = ArmMotion(adapter, self.kin)
        with mock.patch("arm_grasp_pipeline.serial_servo_adapter.time.sleep"):
            snapshot = motion.get_observation_pwm_snapshot()
        self.assertEqual(set(snapshot.pwms), {0, 1, 2, 3, 4})
        self.assertIn(b"#005PRAD!", fake.writes)
        with mock.patch("arm_grasp_pipeline.serial_servo_adapter.time.sleep"):
            with self.assertRaises(PWMReadbackError):
                motion.get_actual_pwm_snapshot()


if __name__ == "__main__":
    unittest.main()
