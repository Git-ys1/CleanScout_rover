import copy
import json
from pathlib import Path
import time

import numpy as np

from arm_grasp_pipeline.arm_motion import ArmMotion
from arm_grasp_pipeline.geometry import (
    CameraIntrinsics,
    FrameTransforms,
    invert_transform,
    transform_point,
)
from arm_grasp_pipeline.grasp_state_machine import DynamicObservation
from arm_grasp_pipeline.official_kinematics import OfficialArmKinematics
from arm_grasp_pipeline.serial_servo_adapter import SerialServoArmAdapter
from arm_grasp_pipeline.target_depth import BBox, DepthObservation


ROOT = Path(__file__).resolve().parents[1]


def runtime_parts(config_mutator=None):
    config = json.loads(
        (ROOT / "config/arm_grasp_default.json").read_text(encoding="utf-8")
    )
    config = copy.deepcopy(config)
    # Synthetic calibrated-looking mount: camera is behind/above the wrist and
    # optical +Z looks along tool +X.  This keeps aligned depth above the real
    # 0.17 m cutoff during final alignment while exercising the same FK chain.
    config["hand_eye"]["T_wrist_camera_color_optical"] = [
        [0.0, 0.0, 1.0, -0.080],
        [-1.0, 0.0, 0.0, 0.0],
        [0.0, -1.0, 0.0, 0.050],
        [0.0, 0.0, 0.0, 1.0],
    ]
    if config_mutator is not None:
        config_mutator(config)
    frames = FrameTransforms.from_config(config)
    kinematics = OfficialArmKinematics.from_config(
        config["kinematics"], config["joint_pwm_calibration"]
    )
    adapter = SerialServoArmAdapter(
        dry_run=True,
        initial_pwms=config["serial"]["initial_dry_run_pwms"],
    )
    arm = ArmMotion(
        adapter,
        kinematics,
        wrist_fixed_pwm=config["grasp"]["wrist_fixed_pwm"],
        servo_pwm_limits=config["grasp"]["servo_pwm_limits"],
    )
    target_center = frames.base_tcp(
        kinematics.forward_wrist_matrix_from_pwm((1481, 1129, 1977, 1646)),
        "closed",
    )[:3, 3]
    # Keep the synthetic bottle comfortably inside the verified-lift
    # workspace.  The previous fixture placed the final TCP at the extreme
    # horizontal reach, so a valid 15 mm vertical verification lift had no IK
    # solution and the test never exercised attachment verification.
    target_center = target_center.copy()
    target_center[0] -= 0.030
    return config, frames, kinematics, adapter, arm, target_center


class StaticTargetSource:
    """Render a static sphere into each new simulated dynamic camera pose."""

    def __init__(
        self,
        adapter,
        kinematics,
        frames,
        target_center,
        radius_m=0.032,
        fail_call=None,
        switch_call=None,
        stale_call=None,
        attach_on_close=False,
        depth_override_m=None,
    ):
        self.adapter = adapter
        self.kinematics = kinematics
        self.frames = frames
        self.target_center = np.asarray(target_center, dtype=float)
        self.radius_m = float(radius_m)
        # Small synthetic focal length keeps the target visible while the
        # test exercises transforms, not a particular physical D435 mount.
        self.intrinsics = CameraIntrinsics(50.0, 50.0, 320.0, 240.0)
        self.fail_call = fail_call
        self.switch_call = switch_call
        self.stale_call = stale_call
        self.attach_on_close = bool(attach_on_close)
        self._T_tcp_object = None
        self.depth_override_m = depth_override_m
        self.calls = []

    def next_observation(self, after_monotonic, expected_track_id):
        call_index = len(self.calls) + 1
        snapshot = self.adapter.read_required_pwms(range(6))
        T_base_wrist = self.kinematics.forward_wrist_matrix_from_pwm(
            snapshot.ordered((0, 1, 2, 3))
        )
        T_base_camera = self.frames.base_camera(T_base_wrist)
        T_base_tcp = self.frames.base_tcp(T_base_wrist, "closed")
        target_center = self.target_center
        if self.attach_on_close and snapshot.pwms[5] >= 2000:
            if self._T_tcp_object is None:
                self._T_tcp_object = np.linalg.inv(T_base_tcp) @ np.array(
                    [*self.target_center, 1.0]
                )
            target_center = (T_base_tcp @ self._T_tcp_object)[:3]
        ray = target_center - T_base_camera[:3, 3]
        ray /= np.linalg.norm(ray)
        surface = target_center - ray * self.radius_m
        point_camera = transform_point(invert_transform(T_base_camera), surface)
        u = self.intrinsics.fx * point_camera[0] / point_camera[2] + self.intrinsics.cx
        v = self.intrinsics.fy * point_camera[1] / point_camera[2] + self.intrinsics.cy
        acquired = (
            float(after_monotonic)
            if call_index == self.stale_call
            else max(time.monotonic(), float(after_monotonic)) + 0.002
        )
        self.calls.append(
            {
                "after": float(after_monotonic),
                "acquired": acquired,
                "pwms": snapshot.ordered(),
            }
        )
        if call_index == self.fail_call:
            return DynamicObservation(
                acquired,
                acquired,
                self.intrinsics,
                (480, 640),
                None,
                None,
                None,
                None,
                False,
                False,
                "synthetic target loss",
            )
        track_id = 2 if call_index == self.switch_call else 1
        switched = call_index == self.switch_call
        bbox = BBox(
            int(round(u - 20)),
            int(round(v - 30)),
            int(round(u + 20)),
            int(round(v + 30)),
            0.95,
            "bottle",
        )
        reported_depth = (
            float(point_camera[2])
            if self.depth_override_m is None
            else float(self.depth_override_m)
        )
        depth = DepthObservation(
            depth_m=reported_depth,
            valid_count=100,
            valid_ratio=1.0,
            median_m=reported_depth,
            mad_m=0.0,
            iqr_m=0.0,
            near_percentile_m=reported_depth,
            roi=(bbox.x1, bbox.y1, bbox.x2, bbox.y2),
            quality_ok=True,
            mode="synthetic",
            pixel_xy=(float(u), float(v)),
            selected_count=100,
            observation_timestamp=acquired,
        )
        return DynamicObservation(
            acquired,
            acquired,
            self.intrinsics,
            (480, 640),
            track_id,
            bbox,
            (float(u), float(v)),
            depth,
            True,
            switched,
            "synthetic track switch" if switched else "associated",
        )
