# coding: utf-8
"""Bounded image-space centering for the eye-in-hand D435 mount."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Sequence, Tuple

from .target_depth import BBox


@dataclass(frozen=True)
class CenteringConfig:
    dead_zone_px: float = 36.0
    yaw_servo_id: int = 0
    pitch_servo_id: int = 3
    yaw_pwm_per_px: float = 0.15
    pitch_pwm_per_px: float = 0.18
    max_pwm_step: int = 12
    yaw_pwm_min: int = 1000
    yaw_pwm_max: int = 2000
    pitch_pwm_min: int = 500
    pitch_pwm_max: int = 1100


class PWMVisualCentering:
    def __init__(self, config: CenteringConfig = CenteringConfig()) -> None:
        self.config = config

    @staticmethod
    def _bounded_step(error_px: float, gain: float, limit: int) -> int:
        raw = int(round(-float(error_px) * float(gain)))
        if raw == 0 and abs(error_px) > 0.5:
            raw = -1 if error_px > 0.0 else 1
        return max(-int(limit), min(int(limit), raw))

    def command(self, target: BBox, frame_shape: Tuple[int, ...], current_pwms: Sequence[int]) -> Dict[int, int]:
        height, width = int(frame_shape[0]), int(frame_shape[1])
        center_x, center_y = target.center
        error_x = center_x - width / 2.0
        error_y = center_y - height / 2.0
        cfg = self.config
        updates: Dict[int, int] = {}

        if abs(error_x) > cfg.dead_zone_px:
            delta = self._bounded_step(error_x, cfg.yaw_pwm_per_px, cfg.max_pwm_step)
            current = int(current_pwms[cfg.yaw_servo_id])
            updates[cfg.yaw_servo_id] = max(cfg.yaw_pwm_min, min(cfg.yaw_pwm_max, current + delta))
        if abs(error_y) > cfg.dead_zone_px:
            delta = self._bounded_step(error_y, cfg.pitch_pwm_per_px, cfg.max_pwm_step)
            current = int(current_pwms[cfg.pitch_servo_id])
            updates[cfg.pitch_servo_id] = max(cfg.pitch_pwm_min, min(cfg.pitch_pwm_max, current + delta))
        return {servo_id: pwm for servo_id, pwm in updates.items() if pwm != int(current_pwms[servo_id])}
