# coding: utf-8
"""Intel RealSense source wrappers with aligned RGB-D freshness evidence.

D435 depth is aligned to the color stream before it is exposed to detection
ROIs.  Each frame carries both the sensor timestamp and an estimated host
monotonic capture timestamp so post-motion code can discard buffered frames.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
import time
from typing import Optional, Sequence

import numpy as np

from .geometry import CameraIntrinsics


class FrameFreshnessError(RuntimeError):
    """A frame is stale, too old, or not valid aligned RGB-D."""


@dataclass
class RealSenseFrame:
    depth_m: np.ndarray
    depth_intrinsics: CameraIntrinsics
    color_bgr: Optional[np.ndarray] = None
    color_intrinsics: Optional[CameraIntrinsics] = None
    monotonic_timestamp: float = field(default_factory=time.monotonic)
    device_timestamp_ms: Optional[float] = None
    arrival_monotonic_timestamp: Optional[float] = None
    depth_aligned_to_color: bool = False
    frame_number: Optional[int] = None
    timestamp_domain: Optional[str] = None

    def __post_init__(self) -> None:
        self.depth_m = np.asarray(self.depth_m)
        if self.depth_m.ndim != 2:
            raise ValueError("RealSense depth_m must be a 2-D image")
        self.monotonic_timestamp = float(self.monotonic_timestamp)
        if not math.isfinite(self.monotonic_timestamp):
            raise ValueError("monotonic_timestamp must be finite")
        if self.arrival_monotonic_timestamp is None:
            self.arrival_monotonic_timestamp = self.monotonic_timestamp
        else:
            self.arrival_monotonic_timestamp = float(self.arrival_monotonic_timestamp)
            if not math.isfinite(self.arrival_monotonic_timestamp):
                raise ValueError("arrival_monotonic_timestamp must be finite")
        if self.monotonic_timestamp > self.arrival_monotonic_timestamp + 1e-6:
            raise ValueError("capture timestamp cannot be later than frame arrival")
        if self.device_timestamp_ms is not None:
            self.device_timestamp_ms = float(self.device_timestamp_ms)
            if not math.isfinite(self.device_timestamp_ms):
                raise ValueError("device_timestamp_ms must be finite")
        if self.color_bgr is not None:
            self.color_bgr = np.asarray(self.color_bgr)
            if self.color_bgr.ndim < 2:
                raise ValueError("color_bgr must be an image")

    @property
    def capture_monotonic_s(self) -> float:
        """Compatibility/descriptive alias for ``monotonic_timestamp``."""
        return float(self.monotonic_timestamp)

    @property
    def observation_timestamp(self) -> float:
        return float(self.monotonic_timestamp)

    @property
    def device_timestamp(self) -> Optional[float]:
        """RealSense device timestamp in milliseconds."""
        return self.device_timestamp_ms

    @property
    def intrinsics_for_detection(self) -> CameraIntrinsics:
        """Use color intrinsics when depth is aligned to color."""
        if self.depth_aligned_to_color:
            if self.color_intrinsics is None:
                raise FrameFreshnessError(
                    "aligned RGB-D frame is missing color intrinsics"
                )
            return self.color_intrinsics
        return self.color_intrinsics or self.depth_intrinsics

    def require_aligned_rgbd(self) -> "RealSenseFrame":
        """Fail unless bbox pixels and depth pixels share the color geometry."""
        if self.color_bgr is None:
            raise FrameFreshnessError("RGB image is missing")
        if self.color_intrinsics is None:
            raise FrameFreshnessError("color intrinsics are missing")
        if not self.depth_aligned_to_color:
            raise FrameFreshnessError("depth has not been aligned to the RGB frame")
        if tuple(self.depth_m.shape[:2]) != tuple(self.color_bgr.shape[:2]):
            raise FrameFreshnessError(
                "aligned depth and RGB image sizes differ: {} vs {}".format(
                    tuple(self.depth_m.shape[:2]), tuple(self.color_bgr.shape[:2])
                )
            )
        return self

    def is_fresh_after(
        self,
        action_end_monotonic_s: float,
        *,
        max_age_s: Optional[float] = None,
        now_monotonic_s: Optional[float] = None,
    ) -> bool:
        """Return true only for a capture strictly after the completed motion."""
        action_end = float(action_end_monotonic_s)
        if not math.isfinite(action_end) or self.monotonic_timestamp <= action_end:
            return False
        if max_age_s is None:
            return True
        now = time.monotonic() if now_monotonic_s is None else float(now_monotonic_s)
        if not math.isfinite(now) or now < self.monotonic_timestamp:
            return False
        return now - self.monotonic_timestamp <= float(max_age_s)

    def require_fresh_after(
        self,
        action_end_monotonic_s: float,
        *,
        max_age_s: Optional[float] = None,
        now_monotonic_s: Optional[float] = None,
    ) -> "RealSenseFrame":
        if not self.is_fresh_after(
            action_end_monotonic_s,
            max_age_s=max_age_s,
            now_monotonic_s=now_monotonic_s,
        ):
            raise FrameFreshnessError(
                "frame {:.6f} is not fresh after motion {:.6f}".format(
                    self.monotonic_timestamp, float(action_end_monotonic_s)
                )
            )
        return self

    assert_fresh_after = require_fresh_after


class RealSenseSource:
    def __init__(
        self,
        width: int = 640,
        height: int = 480,
        fps: int = 30,
        enable_color: bool = True,
        align_depth_to_color: bool = True,
        serial_number: Optional[str] = None,
    ) -> None:
        import pyrealsense2 as rs

        self.rs = rs
        self.width = int(width)
        self.height = int(height)
        self.fps = int(fps)
        self.enable_color = bool(enable_color)
        self.align_depth_to_color = bool(align_depth_to_color and enable_color)
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        if serial_number:
            self.config.enable_device(str(serial_number))
        self.config.enable_stream(
            rs.stream.depth, self.width, self.height, rs.format.z16, self.fps
        )
        if self.enable_color:
            self.config.enable_stream(
                rs.stream.color, self.width, self.height, rs.format.bgr8, self.fps
            )
        self.align = rs.align(rs.stream.color) if self.align_depth_to_color else None
        self.depth_scale: Optional[float] = None
        self._device_to_monotonic_offset_s: Optional[float] = None
        self._last_device_timestamp_s: Optional[float] = None

    def start(self) -> None:
        profile = self.pipeline.start(self.config)
        self.depth_scale = float(
            profile.get_device().first_depth_sensor().get_depth_scale()
        )
        self._device_to_monotonic_offset_s = None
        self._last_device_timestamp_s = None

    @staticmethod
    def _intrinsics(video_frame_profile) -> CameraIntrinsics:
        intr = video_frame_profile.as_video_stream_profile().intrinsics
        return CameraIntrinsics(
            fx=float(intr.fx),
            fy=float(intr.fy),
            cx=float(intr.ppx),
            cy=float(intr.ppy),
        )

    @staticmethod
    def _optional_frame_timestamp_ms(frame) -> Optional[float]:
        if not frame:
            return None
        try:
            value = float(frame.get_timestamp())
        except (AttributeError, RuntimeError, TypeError, ValueError):
            return None
        return value if math.isfinite(value) else None

    @staticmethod
    def _optional_frame_number(frame) -> Optional[int]:
        try:
            return int(frame.get_frame_number())
        except (AttributeError, RuntimeError, TypeError, ValueError):
            return None

    @staticmethod
    def _optional_timestamp_domain(frame) -> Optional[str]:
        try:
            return str(frame.get_frame_timestamp_domain())
        except (AttributeError, RuntimeError, TypeError, ValueError):
            return None

    def _capture_monotonic(
        self, device_timestamp_ms: Optional[float], arrival_monotonic_s: float
    ) -> float:
        if device_timestamp_ms is None:
            return float(arrival_monotonic_s)
        device_s = float(device_timestamp_ms) / 1000.0
        candidate_offset = float(arrival_monotonic_s) - device_s
        # RealSense hardware clocks may reset between stream starts.  A lower
        # offset corresponds to a lower transport latency and is the safe clock
        # mapping for detecting frames buffered before a completed motion.
        if (
            self._last_device_timestamp_s is not None
            and device_s + 0.5 < self._last_device_timestamp_s
        ):
            self._device_to_monotonic_offset_s = candidate_offset
        elif self._device_to_monotonic_offset_s is None:
            self._device_to_monotonic_offset_s = candidate_offset
        else:
            self._device_to_monotonic_offset_s = min(
                self._device_to_monotonic_offset_s, candidate_offset
            )
        self._last_device_timestamp_s = device_s
        mapped = device_s + float(self._device_to_monotonic_offset_s)
        return min(float(arrival_monotonic_s), float(mapped))

    def read(self) -> RealSenseFrame:
        if self.depth_scale is None:
            raise RuntimeError("RealSenseSource.start() must be called before read()")
        frames = self.pipeline.wait_for_frames()
        if self.align is not None:
            frames = self.align.process(frames)
        depth_frame = frames.get_depth_frame()
        if not depth_frame:
            raise RuntimeError("RealSense returned no depth frame")
        depth_raw = np.asanyarray(depth_frame.get_data())
        depth_m = depth_raw.astype(np.float32) * self.depth_scale
        depth_intr = self._intrinsics(depth_frame.profile)

        color_bgr = None
        color_intr = None
        color_frame = None
        if self.enable_color:
            color_frame = frames.get_color_frame()
            if not color_frame:
                raise RuntimeError(
                    "RealSense color stream was enabled but returned no color frame"
                )
            color_bgr = np.asanyarray(color_frame.get_data())
            color_intr = self._intrinsics(color_frame.profile)
            if self.align_depth_to_color and depth_m.shape[:2] != color_bgr.shape[:2]:
                raise RuntimeError(
                    "RealSense aligned depth/color shapes differ: {} vs {}".format(
                        depth_m.shape[:2], color_bgr.shape[:2]
                    )
                )

        arrival = time.monotonic()
        device_timestamps = [
            value
            for value in (
                self._optional_frame_timestamp_ms(depth_frame),
                self._optional_frame_timestamp_ms(color_frame),
            )
            if value is not None
        ]
        # Use the earlier member of the RGB-D pair: both observations must be
        # newer than a motion before their aligned pixels may drive the robot.
        device_timestamp_ms = min(device_timestamps) if device_timestamps else None
        capture = self._capture_monotonic(device_timestamp_ms, arrival)

        return RealSenseFrame(
            depth_m=depth_m,
            depth_intrinsics=depth_intr,
            color_bgr=color_bgr,
            color_intrinsics=color_intr,
            monotonic_timestamp=capture,
            device_timestamp_ms=device_timestamp_ms,
            arrival_monotonic_timestamp=arrival,
            depth_aligned_to_color=bool(self.align_depth_to_color),
            frame_number=self._optional_frame_number(depth_frame),
            timestamp_domain=self._optional_timestamp_domain(depth_frame),
        )

    def read_fresh_after(
        self,
        action_end_monotonic_s: float,
        *,
        max_age_s: Optional[float] = None,
        max_discarded_frames: int = 120,
        require_aligned_rgbd: Optional[bool] = None,
    ) -> RealSenseFrame:
        """Discard queued frames until a strictly post-motion capture arrives."""
        limit = int(max_discarded_frames)
        if limit < 0:
            raise ValueError("max_discarded_frames must be non-negative")
        require_aligned = (
            self.align_depth_to_color
            if require_aligned_rgbd is None
            else bool(require_aligned_rgbd)
        )
        for _ in range(limit + 1):
            frame = self.read()
            if not frame.is_fresh_after(
                action_end_monotonic_s,
                max_age_s=max_age_s,
                now_monotonic_s=frame.arrival_monotonic_timestamp,
            ):
                continue
            if require_aligned:
                frame.require_aligned_rgbd()
            return frame
        raise FrameFreshnessError(
            "no fresh RealSense frame after {:.6f} within {} discarded frames".format(
                float(action_end_monotonic_s), limit
            )
        )

    def stop(self) -> None:
        self.pipeline.stop()


class D435Source(RealSenseSource):
    def __init__(
        self,
        width: int = 640,
        height: int = 480,
        fps: int = 30,
        serial_number: Optional[str] = None,
    ) -> None:
        super().__init__(
            width=width,
            height=height,
            fps=fps,
            enable_color=True,
            align_depth_to_color=True,
            serial_number=serial_number,
        )


class D430DepthSource(RealSenseSource):
    def __init__(
        self,
        width: int = 640,
        height: int = 480,
        fps: int = 30,
        serial_number: Optional[str] = None,
    ) -> None:
        super().__init__(
            width=width,
            height=height,
            fps=fps,
            enable_color=False,
            align_depth_to_color=False,
            serial_number=serial_number,
        )


__all__ = [
    "D430DepthSource",
    "D435Source",
    "FrameFreshnessError",
    "RealSenseFrame",
    "RealSenseSource",
]
