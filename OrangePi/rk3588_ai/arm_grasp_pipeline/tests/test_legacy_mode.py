from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np

from arm_grasp_pipeline.arm_motion import MotionResult
from arm_grasp_pipeline.geometry import CameraIntrinsics
from arm_grasp_pipeline.legacy_fixed_view_runtime import (
    LegacyFixedViewSafetyError,
    LegacyFixedViewWarning,
    LegacyObservation,
    maybe_run_legacy_fixed_view,
    run_legacy_fixed_view,
)
from arm_grasp_pipeline.serial_servo_adapter import (
    PWMReadbackSnapshot,
    SerialServoArmAdapter,
)


CONFIG_PATH = Path(__file__).resolve().parents[1] / "config/arm_grasp_default.json"


class FakeKinematics:
    def inverse_pose(self, xyz_m, pitch_deg=0.0, gripper=0.0):
        del pitch_deg, gripper
        xyz = np.asarray(xyz_m, dtype=float)
        # Distinct but bounded values let the stage PRAD test detect whether
        # every expected axis is checked.
        pwms = (
            1500,
            1700 + int(round(xyz[0] * 10.0)),
            1800,
            700,
        )
        return SimpleNamespace(
            joints_rad=(0.0, 0.1, 0.2, 0.3),
            servo_angles_deg=(0.0, 1.0, 2.0, 3.0),
            servo_pwms=pwms,
        )


class TrackingAdapter(SerialServoArmAdapter):
    def __init__(self, dry_run, initial_pwms):
        super().__init__(
            dry_run=dry_run,
            initial_pwms=initial_pwms,
            motion_settle_s=0.0,
        )
        self.connect_calls = 0
        self.close_calls = 0
        self.stop_calls = 0

    def connect(self):
        self.connect_calls += 1
        if self.dry_run:
            raise AssertionError("dry-run must not open the serial transport")

    def close(self):
        self.close_calls += 1

    def send_stop(self, servo_ids=None):
        self.stop_calls += 1
        raise AssertionError("legacy runtime must never send PDST")


class FakeRealArm:
    def __init__(self, adapter, kinematics, reference_pwms, stage_pwms=None):
        self.adapter = adapter
        self.kin = kinematics
        self.reference_pwms = tuple(reference_pwms)
        self.stage_pwms = tuple(stage_pwms or reference_pwms)
        self.executions = 0

    @staticmethod
    def _snapshot(values):
        return PWMReadbackSnapshot(
            {index: int(value) for index, value in enumerate(values)},
            monotonic_timestamp=1.0,
            attempts=1,
            simulated=False,
        )

    def get_actual_pwm_snapshot(self):
        return self._snapshot(self.reference_pwms)

    def pack_ik_command(self, ik, duration_ms):
        del ik
        return "#FAKEIKT{:04d}!".format(int(duration_ms))

    def execute_assignments(self, assignments, duration_ms):
        del assignments, duration_ms
        self.executions += 1
        return MotionResult(
            ok=True,
            ik=None,
            command_packed=True,
            command_written=True,
            readback_reached=True,
            readback_snapshot=self._snapshot(self.stage_pwms),
        )

    def execute_ik(self, ik, duration_ms):
        del ik, duration_ms
        self.executions += 1
        return MotionResult(
            ok=True,
            ik=None,
            command_packed=True,
            command_written=True,
            readback_reached=True,
            readback_snapshot=self._snapshot(self.stage_pwms),
        )


def load_test_config():
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    config = copy.deepcopy(config)
    # Make the pure test observation map to base [0.25, 0, 0.10].
    config["fixed_view_calibration"].update(
        {
            "calibrated": True,
            "base_to_camera_matrix_4x4": [
                [1.0, 0.0, 0.0, 0.25],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, -0.10],
                [0.0, 0.0, 0.0, 1.0],
            ],
            "rmse_m": 0.001,
            "max_error_m": 0.002,
        }
    )
    return config


def observation():
    return LegacyObservation(
        pixel_xy=(320.0, 240.0),
        depth_m=0.20,
        intrinsics=CameraIntrinsics(fx=600.0, fy=600.0, cx=320.0, cy=240.0),
    )


def args(**overrides):
    values = {
        "mode": "legacy_fixed_view",
        "dry_run": True,
        "enable_arm": False,
        "max_stage": "pregrasp",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class LegacySelectionTests(unittest.TestCase):
    def test_default_dynamic_mode_does_not_enter_or_warn(self):
        provider = mock.Mock(side_effect=AssertionError("must not be called"))
        with warnings_capture() as caught:
            result = maybe_run_legacy_fixed_view(
                args(mode="observe"),
                {},
                {"observation_provider": provider},
            )
        self.assertIsNone(result)
        provider.assert_not_called()
        self.assertEqual(caught, [])

    def test_explicit_entry_emits_visible_deprecation_warning(self):
        config = load_test_config()
        adapter = TrackingAdapter(
            True, config["fixed_view_calibration"]["reference_servo_pwms"]
        )
        with warnings_capture() as caught:
            result = run_legacy_fixed_view(
                args(),
                config,
                {
                    "observation": observation(),
                    "kinematics": FakeKinematics(),
                    "adapter": adapter,
                },
            )
        self.assertEqual(result, 0)
        self.assertTrue(
            any(issubclass(item.category, LegacyFixedViewWarning) for item in caught)
        )

    def test_dry_run_plans_and_simulates_without_opening_serial_or_pdst(self):
        config = load_test_config()
        adapter = TrackingAdapter(
            True, config["fixed_view_calibration"]["reference_servo_pwms"]
        )
        with warnings_capture():
            result = run_legacy_fixed_view(
                args(max_stage="approach"),
                config,
                {
                    "observation": observation(),
                    "kinematics": FakeKinematics(),
                    "adapter": adapter,
                },
            )
        self.assertEqual(result, 0)
        self.assertEqual(adapter.connect_calls, 0)
        self.assertEqual(adapter.stop_calls, 0)
        self.assertEqual(adapter.close_calls, 1)


class LegacyRealMotionGateTests(unittest.TestCase):
    def test_real_mode_requires_enable_arm_before_connect_or_observation(self):
        config = load_test_config()
        adapter = TrackingAdapter(
            False, config["fixed_view_calibration"]["reference_servo_pwms"]
        )
        provider = mock.Mock(side_effect=AssertionError("must fail before observation"))
        with warnings_capture(), self.assertRaisesRegex(
            LegacyFixedViewSafetyError, "enable_arm"
        ):
            run_legacy_fixed_view(
                args(dry_run=False, enable_arm=False),
                config,
                {
                    "observation_provider": provider,
                    "kinematics": FakeKinematics(),
                    "adapter": adapter,
                },
            )
        self.assertEqual(adapter.connect_calls, 0)
        provider.assert_not_called()

    def test_real_mode_requires_calibrated_fixed_view_before_connect(self):
        config = load_test_config()
        config["fixed_view_calibration"]["calibrated"] = False
        adapter = TrackingAdapter(
            False, config["fixed_view_calibration"]["reference_servo_pwms"]
        )
        with warnings_capture(), self.assertRaisesRegex(
            LegacyFixedViewSafetyError, "calibrated is false"
        ):
            run_legacy_fixed_view(
                args(dry_run=False, enable_arm=True),
                config,
                {"kinematics": FakeKinematics(), "adapter": adapter},
            )
        self.assertEqual(adapter.connect_calls, 0)

    def test_real_stage_rejects_missing_target_pwms_even_after_ok_result(self):
        config = load_test_config()
        reference = config["fixed_view_calibration"]["reference_servo_pwms"]
        adapter = TrackingAdapter(False, reference)
        # Reference PRAD passes, but OPEN expects Servo005=1000 and this stale
        # snapshot reports 1500.  A successful serial write is still failure.
        arm = FakeRealArm(adapter, FakeKinematics(), reference, stage_pwms=reference)
        with warnings_capture(), self.assertRaisesRegex(
            LegacyFixedViewSafetyError, "PRAD stage mismatch"
        ):
            run_legacy_fixed_view(
                args(dry_run=False, enable_arm=True, max_stage="open"),
                config,
                {
                    "observation": observation(),
                    "kinematics": arm.kin,
                    "adapter": adapter,
                    "arm": arm,
                },
            )
        self.assertEqual(adapter.connect_calls, 1)
        self.assertEqual(arm.executions, 1)
        self.assertEqual(adapter.stop_calls, 0)


class warnings_capture:
    def __enter__(self):
        self._context = unittest.mock.patch("warnings.showwarning")
        # Use the real registry/filter machinery but collect WarningMessage
        # objects; simplefilter(always) also proves our RuntimeWarning is visible.
        self._catch = __import__("warnings").catch_warnings(record=True)
        self.messages = self._catch.__enter__()
        __import__("warnings").simplefilter("always")
        return self.messages

    def __exit__(self, exc_type, exc, tb):
        return self._catch.__exit__(exc_type, exc, tb)


if __name__ == "__main__":
    unittest.main()
