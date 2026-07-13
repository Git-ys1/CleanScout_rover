# coding: utf-8
"""Intel RealSense source wrappers for D430/D435.

D435 path: depth aligned to color, intended for YOLO color bbox + depth ROI.
D430 path: depth-only smoke/test path, intended to validate intrinsics, ROI depth,
and pixel/depth projection before the D435 RGB stream arrives.

The rest of the grasp pipeline consumes metres and CameraIntrinsics only; it does
not care whether the depth came from D430 or D435.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from .geometry import CameraIntrinsics


@dataclass
class RealSenseFrame:
    depth_m: np.ndarray
    depth_intrinsics: CameraIntrinsics
    color_bgr: Optional[np.ndarray] = None
    color_intrinsics: Optional[CameraIntrinsics] = None

    @property
    def intrinsics_for_detection(self) -> CameraIntrinsics:
        """Use color intrinsics when depth is aligned to color, else depth intrinsics."""
        return self.color_intrinsics or self.depth_intrinsics


class RealSenseSource:
    def __init__(self, width: int = 640, height: int = 480, fps: int = 30,
                 enable_color: bool = True, align_depth_to_color: bool = True,
                 serial_number: Optional[str] = None) -> None:
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
        self.config.enable_stream(rs.stream.depth, self.width, self.height, rs.format.z16, self.fps)
        if self.enable_color:
            self.config.enable_stream(rs.stream.color, self.width, self.height, rs.format.bgr8, self.fps)
        self.align = rs.align(rs.stream.color) if self.align_depth_to_color else None
        self.depth_scale: Optional[float] = None

    def start(self) -> None:
        profile = self.pipeline.start(self.config)
        self.depth_scale = float(profile.get_device().first_depth_sensor().get_depth_scale())

    @staticmethod
    def _intrinsics(video_frame_profile) -> CameraIntrinsics:
        intr = video_frame_profile.as_video_stream_profile().intrinsics
        return CameraIntrinsics(fx=float(intr.fx), fy=float(intr.fy), cx=float(intr.ppx), cy=float(intr.ppy))

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
        if self.enable_color:
            color_frame = frames.get_color_frame()
            if not color_frame:
                raise RuntimeError("RealSense color stream was enabled but returned no color frame")
            color_bgr = np.asanyarray(color_frame.get_data())
            color_intr = self._intrinsics(color_frame.profile)

        return RealSenseFrame(
            depth_m=depth_m,
            depth_intrinsics=depth_intr,
            color_bgr=color_bgr,
            color_intrinsics=color_intr,
        )

    def stop(self) -> None:
        self.pipeline.stop()


class D435Source(RealSenseSource):
    def __init__(self, width: int = 640, height: int = 480, fps: int = 30,
                 serial_number: Optional[str] = None) -> None:
        super().__init__(width=width, height=height, fps=fps, enable_color=True,
                         align_depth_to_color=True, serial_number=serial_number)


class D430DepthSource(RealSenseSource):
    def __init__(self, width: int = 640, height: int = 480, fps: int = 30,
                 serial_number: Optional[str] = None) -> None:
        super().__init__(width=width, height=height, fps=fps, enable_color=False,
                         align_depth_to_color=False, serial_number=serial_number)
