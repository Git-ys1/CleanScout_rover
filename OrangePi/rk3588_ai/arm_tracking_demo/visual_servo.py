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
    dead_zone_px: int = 42
    control_rate_hz: float = 12.0
    max_yaw_delta: float = 0.018
    max_lift_delta: float = 0.006
    max_pitch_delta: float = 0.012
    error_filter_alpha: float = 0.6
    confirm_frames: int = 2
    lost_hold_frames: int = 5
    lost_stop_frames: int = 15
    yaw_init: float = 0.0
    lift_init: float = -0.930
    pitch_init: float = 1.2
    yaw_min: float = -0.5
    yaw_max: float = 0.5
    lift_min: float = -1.20
    lift_max: float = -0.65
    pitch_min: float = 0.9
    pitch_max: float = 1.5
    kp_yaw: float = 0.0009
    ki_yaw: float = 0.0
    kd_yaw: float = 0.0
    kp_lift: float = 0.00045
    ki_lift: float = 0.0
    kd_lift: float = 0.0
    kp_pitch: float = 0.00065
    ki_pitch: float = 0.0
    kd_pitch: float = 0.0
    invert_yaw: bool = True
    invert_lift: bool = True
    invert_pitch: bool = False
    control_axes: Sequence[str] = ("yaw", "lift", "pitch")
    combined_lift_error_px: int = 80
    combined_lift_rate_divider: int = 4


def normalize_control_axes(value) -> Tuple[str, ...]:
    if isinstance(value, str):
        raw_axes = value.replace(";", ",").split(",")
    else:
        raw_axes = list(value or ())

    aliases = {
        "yaw": "yaw",
        "servo0": "yaw",
        "joint0": "yaw",
        "lift": "lift",
        "servo1": "lift",
        "joint1": "lift",
        "pitch": "pitch",
        "servo3": "pitch",
        "joint3": "pitch",
    }

    axes = []
    for axis in raw_axes:
        axis = str(axis).strip().lower()
        normalized = aliases.get(axis)
        if normalized and normalized not in axes:
            axes.append(normalized)
    return tuple(axes)


class VisualServo:
    def __init__(self, config: Optional[VisualServoConfig] = None):
        self.config = config or VisualServoConfig()
        self.control_axes = normalize_control_axes(self.config.control_axes)
        self.yaw = self.config.yaw_init
        self.lift = self.config.lift_init
        self.pitch = self.config.pitch_init
        self.joints = self._make_base_joints()
        self.confirm_count = 0
        self.lost_count = 0
        self.last_control_time = 0.0
        self.integral_x = 0.0
        self.integral_lift = 0.0
        self.integral_y = 0.0
        self.prev_error_x = 0.0
        self.prev_error_lift = 0.0
        self.prev_error_y = 0.0
        self.control_tick_count = 0
        self.last_lift_error_y = 0.0
        self.last_pitch_error_y = 0.0
        self.last_command_axes = tuple(self.control_axes)
        self.filtered_error_x = 0.0
        self.filtered_error_y = 0.0
        self.error_filter_ready = False
        self.last_result = self._result(None, None, 0.0, 0.0, False, False)

    def reset(self):
        self.yaw = self.config.yaw_init
        self.lift = self.config.lift_init
        self.pitch = self.config.pitch_init
        self.joints = self._make_base_joints()
        self.confirm_count = 0
        self.lost_count = 0
        self.integral_x = 0.0
        self.integral_lift = 0.0
        self.integral_y = 0.0
        self.prev_error_x = 0.0
        self.prev_error_lift = 0.0
        self.prev_error_y = 0.0
        self.control_tick_count = 0
        self.last_lift_error_y = 0.0
        self.last_pitch_error_y = 0.0
        self.last_command_axes = tuple(self.control_axes)
        self.filtered_error_x = 0.0
        self.filtered_error_y = 0.0
        self.error_filter_ready = False
        self.last_control_time = 0.0
        self.last_result = self._result(None, None, 0.0, 0.0, False, False)

    def _make_base_joints(self):
        joints = list(self.config.base_joints)
        if len(joints) < 6:
            joints.extend([0.0] * (6 - len(joints)))
        joints = joints[:6]
        joints[0] = self.yaw
        joints[1] = self.lift
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
            if self.lost_count >= self.config.lost_hold_frames:
                self.error_filter_ready = False
            active = self.lost_count < self.config.lost_stop_frames
            self.last_result = self._result(None, None, 0.0, 0.0, active, False)
            return self.last_result

        self.lost_count = 0
        self.confirm_count += 1
        cx = (float(target_box[0]) + float(target_box[2])) / 2.0
        cy = (float(target_box[1]) + float(target_box[3])) / 2.0
        raw_error_x = cx - (float(frame_width) / 2.0)
        raw_error_y = cy - (float(frame_height) / 2.0)
        error_x, error_y = self._filter_error(raw_error_x, raw_error_y)

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
        self.last_result["raw_error_x"] = raw_error_x
        self.last_result["raw_error_y"] = raw_error_y
        return self.last_result

    def _filter_error(self, raw_error_x: float, raw_error_y: float) -> Tuple[float, float]:
        alpha = clamp(float(self.config.error_filter_alpha), 0.0, 0.95)
        if not self.error_filter_ready:
            self.filtered_error_x = raw_error_x
            self.filtered_error_y = raw_error_y
            self.error_filter_ready = True
        else:
            self.filtered_error_x = (alpha * self.filtered_error_x) + ((1.0 - alpha) * raw_error_x)
            self.filtered_error_y = (alpha * self.filtered_error_y) + ((1.0 - alpha) * raw_error_y)
        return self.filtered_error_x, self.filtered_error_y

    def _step(self, error_x: float, error_y: float, dt: float):
        self.control_tick_count += 1
        effective_x = 0.0 if abs(error_x) < self.config.dead_zone_px else error_x
        effective_y = 0.0 if abs(error_y) < self.config.dead_zone_px else error_y
        pitch_error_y = effective_y
        lift_error_y = self._lift_error_for_step(effective_y)
        self.last_pitch_error_y = pitch_error_y
        self.last_lift_error_y = lift_error_y
        command_axes = []

        if "yaw" in self.control_axes:
            self.integral_x += effective_x * dt
            derivative_x = (effective_x - self.prev_error_x) / dt
            self.prev_error_x = effective_x
            command_axes.append("yaw")
        else:
            self.integral_x = 0.0
            derivative_x = 0.0
            self.prev_error_x = 0.0

        if "lift" in self.control_axes and lift_error_y != 0.0:
            self.integral_lift += lift_error_y * dt
            derivative_lift = (lift_error_y - self.prev_error_lift) / dt
            self.prev_error_lift = lift_error_y
            command_axes.append("lift")
        else:
            self.integral_lift = 0.0
            derivative_lift = 0.0
            self.prev_error_lift = 0.0

        if "pitch" in self.control_axes:
            self.integral_y += pitch_error_y * dt
            derivative_y = (pitch_error_y - self.prev_error_y) / dt
            self.prev_error_y = pitch_error_y
            command_axes.append("pitch")
        else:
            self.integral_y = 0.0
            derivative_y = 0.0
            self.prev_error_y = 0.0
        self.last_command_axes = tuple(command_axes)

        yaw_delta = (
            self.config.kp_yaw * effective_x
            + self.config.ki_yaw * self.integral_x
            + self.config.kd_yaw * derivative_x
        )
        lift_delta = (
            self.config.kp_lift * lift_error_y
            + self.config.ki_lift * self.integral_lift
            + self.config.kd_lift * derivative_lift
        )
        pitch_delta = (
            self.config.kp_pitch * pitch_error_y
            + self.config.ki_pitch * self.integral_y
            + self.config.kd_pitch * derivative_y
        )

        if self.config.invert_yaw:
            yaw_delta = -yaw_delta
        if self.config.invert_lift:
            lift_delta = -lift_delta
        if self.config.invert_pitch:
            pitch_delta = -pitch_delta

        yaw_delta = clamp(yaw_delta, -self.config.max_yaw_delta, self.config.max_yaw_delta)
        lift_delta = clamp(lift_delta, -self.config.max_lift_delta, self.config.max_lift_delta)
        pitch_delta = clamp(pitch_delta, -self.config.max_pitch_delta, self.config.max_pitch_delta)
        if "yaw" in self.control_axes:
            self.yaw = clamp(self.yaw + yaw_delta, self.config.yaw_min, self.config.yaw_max)
        if "lift" in self.control_axes:
            self.lift = clamp(self.lift + lift_delta, self.config.lift_min, self.config.lift_max)
        if "pitch" in self.control_axes:
            self.pitch = clamp(self.pitch + pitch_delta, self.config.pitch_min, self.config.pitch_max)
        self.joints[0] = self.yaw
        self.joints[1] = self.lift
        self.joints[3] = self.pitch

    def _lift_error_for_step(self, effective_y: float) -> float:
        """In combined tracking, Servo003 handles fine pitch first.

        Servo001 changes the whole arm posture and load, so it only joins in
        for large vertical errors and at a lower update rate. This prevents
        lift and pitch from fighting over the same camera-space error.
        """
        combined_vertical = "lift" in self.control_axes and "pitch" in self.control_axes
        if not combined_vertical:
            return effective_y
        threshold = max(int(self.config.combined_lift_error_px), int(self.config.dead_zone_px))
        if abs(effective_y) < threshold:
            return 0.0
        divider = max(1, int(self.config.combined_lift_rate_divider))
        if self.control_tick_count % divider != 0:
            return 0.0
        return effective_y

    def _result(self, cx, cy, error_x, error_y, active: bool, should_send: bool):
        return {
            "yaw": self.yaw,
            "lift": self.lift,
            "pitch": self.pitch,
            "joints": list(self.joints),
            "cx": cx,
            "cy": cy,
            "error_x": error_x,
            "error_y": error_y,
            "raw_error_x": error_x,
            "raw_error_y": error_y,
            "active": active,
            "should_send": should_send,
            "confirm_count": self.confirm_count,
            "lost_count": self.lost_count,
            "control_axes": list(self.control_axes),
            "command_axes": list(self.last_command_axes),
            "combined_vertical": "lift" in self.control_axes and "pitch" in self.control_axes,
            "lift_error_y": self.last_lift_error_y,
            "pitch_error_y": self.last_pitch_error_y,
        }


def config_from_mapping(values: Optional[Dict[str, object]]) -> VisualServoConfig:
    if not values:
        return VisualServoConfig()
    valid = {field.name for field in VisualServoConfig.__dataclass_fields__.values()}
    filtered = {key: values[key] for key in values if key in valid}
    return VisualServoConfig(**filtered)
