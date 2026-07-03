#!/usr/bin/env python3
"""2D visual-servo controller for YOLO target boxes."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Optional, Sequence, Tuple


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


@dataclass
class VisualServoConfig:
    base_joints: Sequence[float] = (0.0, -0.930, 1.6, 1.2, 0.0, 0.801)
    dead_zone_px: int = 30
    control_rate_hz: float = 10.0
    max_yaw_delta: float = 0.015
    max_pitch_delta: float = 0.015
    confirm_frames: int = 2
    lost_hold_frames: int = 5
    lost_stop_frames: int = 15
    yaw_init: float = 0.0
    pitch_init: float = 1.2
    yaw_min: float = -0.5
    yaw_max: float = 0.5
    pitch_min: float = 0.9
    pitch_max: float = 1.5
    kp_yaw: float = 0.0008
    ki_yaw: float = 0.0
    kd_yaw: float = 0.0
    kp_pitch: float = 0.0008
    ki_pitch: float = 0.0
    kd_pitch: float = 0.0
    invert_yaw: bool = True
    invert_pitch: bool = True
    control_axes: Sequence[str] = ("yaw", "pitch")


def normalize_control_axes(value) -> Tuple[str, ...]:
    if isinstance(value, str):
        raw_axes = value.replace(";", ",").split(",")
    else:
        raw_axes = list(value or ())

    axes = []
    for axis in raw_axes:
        axis = str(axis).strip().lower()
        if axis in ("yaw", "pitch") and axis not in axes:
            axes.append(axis)
    return tuple(axes)


class VisualServo:
    def __init__(self, config: Optional[VisualServoConfig] = None):
        self.config = config or VisualServoConfig()
        self.control_axes = normalize_control_axes(self.config.control_axes)
        self.yaw = self.config.yaw_init
        self.pitch = self.config.pitch_init
        self.joints = self._make_base_joints()
        self.confirm_count = 0
        self.lost_count = 0
        self.last_control_time = 0.0
        self.integral_x = 0.0
        self.integral_y = 0.0
        self.prev_error_x = 0.0
        self.prev_error_y = 0.0
        self.last_result = self._result(None, None, 0.0, 0.0, False, False)

    def reset(self):
        self.yaw = self.config.yaw_init
        self.pitch = self.config.pitch_init
        self.joints = self._make_base_joints()
        self.confirm_count = 0
        self.lost_count = 0
        self.integral_x = 0.0
        self.integral_y = 0.0
        self.prev_error_x = 0.0
        self.prev_error_y = 0.0
        self.last_control_time = 0.0
        self.last_result = self._result(None, None, 0.0, 0.0, False, False)

    def _make_base_joints(self):
        joints = list(self.config.base_joints)
        if len(joints) < 6:
            joints.extend([0.0] * (6 - len(joints)))
        joints = joints[:6]
        joints[0] = self.yaw
        joints[3] = self.pitch
        return joints

    def update(
        self,
        target_box: Optional[Sequence[float]],
        frame_width: int,
        frame_height: int,
        now: Optional[float] = None,
    ) -> Dict[str, object]:
        now = time.monotonic() if now is None else now

        if target_box is None:
            self.lost_count += 1
            self.confirm_count = 0
            active = self.lost_count < self.config.lost_stop_frames
            self.last_result = self._result(None, None, 0.0, 0.0, active, False)
            return self.last_result

        self.lost_count = 0
        self.confirm_count += 1
        cx = (float(target_box[0]) + float(target_box[2])) / 2.0
        cy = (float(target_box[1]) + float(target_box[3])) / 2.0
        error_x = cx - (float(frame_width) / 2.0)
        error_y = cy - (float(frame_height) / 2.0)

        target_confirmed = self.confirm_count >= self.config.confirm_frames
        min_period = 1.0 / max(self.config.control_rate_hz, 0.1)
        rate_ready = (now - self.last_control_time) >= min_period
        should_send = False

        if target_confirmed and rate_ready:
            dt = max(now - self.last_control_time, min_period)
            self.last_control_time = now
            self._step(error_x, error_y, dt)
            should_send = True

        self.last_result = self._result(cx, cy, error_x, error_y, True, should_send)
        return self.last_result

    def _step(self, error_x: float, error_y: float, dt: float):
        effective_x = 0.0 if abs(error_x) < self.config.dead_zone_px else error_x
        effective_y = 0.0 if abs(error_y) < self.config.dead_zone_px else error_y

        if "yaw" in self.control_axes:
            self.integral_x += effective_x * dt
            derivative_x = (effective_x - self.prev_error_x) / dt
            self.prev_error_x = effective_x
        else:
            self.integral_x = 0.0
            derivative_x = 0.0
            self.prev_error_x = 0.0

        if "pitch" in self.control_axes:
            self.integral_y += effective_y * dt
            derivative_y = (effective_y - self.prev_error_y) / dt
            self.prev_error_y = effective_y
        else:
            self.integral_y = 0.0
            derivative_y = 0.0
            self.prev_error_y = 0.0

        yaw_delta = (
            self.config.kp_yaw * effective_x
            + self.config.ki_yaw * self.integral_x
            + self.config.kd_yaw * derivative_x
        )
        pitch_delta = (
            self.config.kp_pitch * effective_y
            + self.config.ki_pitch * self.integral_y
            + self.config.kd_pitch * derivative_y
        )

        if self.config.invert_yaw:
            yaw_delta = -yaw_delta
        if self.config.invert_pitch:
            pitch_delta = -pitch_delta

        yaw_delta = clamp(yaw_delta, -self.config.max_yaw_delta, self.config.max_yaw_delta)
        pitch_delta = clamp(pitch_delta, -self.config.max_pitch_delta, self.config.max_pitch_delta)
        if "yaw" in self.control_axes:
            self.yaw = clamp(self.yaw + yaw_delta, self.config.yaw_min, self.config.yaw_max)
        if "pitch" in self.control_axes:
            self.pitch = clamp(self.pitch + pitch_delta, self.config.pitch_min, self.config.pitch_max)
        self.joints[0] = self.yaw
        self.joints[3] = self.pitch

    def _result(self, cx, cy, error_x, error_y, active: bool, should_send: bool):
        return {
            "yaw": self.yaw,
            "pitch": self.pitch,
            "joints": list(self.joints),
            "cx": cx,
            "cy": cy,
            "error_x": error_x,
            "error_y": error_y,
            "active": active,
            "should_send": should_send,
            "confirm_count": self.confirm_count,
            "lost_count": self.lost_count,
            "control_axes": list(self.control_axes),
        }


def config_from_mapping(values: Optional[Dict[str, object]]) -> VisualServoConfig:
    if not values:
        return VisualServoConfig()
    valid = {field.name for field in VisualServoConfig.__dataclass_fields__.values()}
    filtered = {key: values[key] for key in values if key in valid}
    return VisualServoConfig(**filtered)
