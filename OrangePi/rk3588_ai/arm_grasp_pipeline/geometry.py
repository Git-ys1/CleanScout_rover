# coding: utf-8
"""Camera geometry and hand-eye transforms for D430/D435 grasping.

The formulas mirror the uploaded Raspberry Pi ROS2 transform.py and
arm_ik_sdk.py, but this file is ROS-free and can run on OrangePi directly.
The public functions intentionally stay message-agnostic so a later ROS adapter
can publish the same outputs without rewriting geometry.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Optional, Tuple

import numpy as np


@dataclass(frozen=True)
class CameraIntrinsics:
    fx: float
    fy: float
    cx: float
    cy: float


@dataclass(frozen=True)
class HandEye:
    # Learning package matrix_hand_to_cam, metres. Treat as calibration seed only.
    x: float = -0.055
    y: float = 0.011
    z: float = -0.00224
    roll_deg: float = 0.0
    pitch_deg: float = 0.0
    yaw_deg: float = 0.0

    def matrix(self) -> np.ndarray:
        T = euler_xyz_to_matrix((self.x, self.y, self.z), (self.roll_deg, self.pitch_deg, self.yaw_deg))
        return T


@dataclass(frozen=True)
class PixelToBaseDebug:
    pixel_xy: Tuple[float, float]
    depth_m: float
    point_camera_m: Tuple[float, float, float]
    point_arm_camera_axes_m: Tuple[float, float, float]
    point_base_m: Tuple[float, float, float]


def depth_pixel_to_camera(pixel_xy: Tuple[float, float], depth_m: float, intr: CameraIntrinsics) -> np.ndarray:
    u, v = pixel_xy
    z = float(depth_m)
    x = (float(u) - intr.cx) * z / intr.fx
    y = (float(v) - intr.cy) * z / intr.fy
    return np.array([x, y, z], dtype=float)


def matrix_from_translation_rotation(xyz: Iterable[float], R: Optional[np.ndarray] = None) -> np.ndarray:
    T = np.eye(4, dtype=float)
    if R is not None:
        R = np.asarray(R, dtype=float)
        if R.shape != (3, 3):
            raise ValueError("R must be 3x3")
        T[:3, :3] = R
    T[:3, 3] = [float(v) for v in xyz]
    return T


def euler_xyz_to_matrix(xyz: Iterable[float], euler_deg=(0.0, 0.0, 0.0)) -> np.ndarray:
    x, y, z = [float(v) for v in xyz]
    rx, ry, rz = [math.radians(float(v)) for v in euler_deg]
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]], dtype=float)
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], dtype=float)
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]], dtype=float)
    return matrix_from_translation_rotation((x, y, z), Rz @ Ry @ Rx)


def invert_transform(T: np.ndarray) -> np.ndarray:
    T = np.asarray(T, dtype=float)
    if T.shape != (4, 4):
        raise ValueError("T must be 4x4")
    out = np.eye(4, dtype=float)
    R = T[:3, :3]
    t = T[:3, 3]
    out[:3, :3] = R.T
    out[:3, 3] = -R.T @ t
    return out


def transform_point(T: np.ndarray, point_xyz: Iterable[float]) -> np.ndarray:
    p = np.array([float(v) for v in point_xyz] + [1.0], dtype=float)
    return (np.asarray(T, dtype=float) @ p)[:3]


def d435_point_to_arm_camera_axes(point_cam: np.ndarray) -> np.ndarray:
    """Match the axis remap used by dynamic_space_grab.py.

    Source package did:
      temp = position[0]
      position[0] = position[1]
      position[1] = -temp
    """
    x, y, z = [float(v) for v in point_cam]
    return np.array([y, -x, z], dtype=float)


def target_pixel_to_base_point_debug(
    pixel_xy: Tuple[float, float],
    depth_m: float,
    intr: CameraIntrinsics,
    T_base_ee: np.ndarray,
    hand_eye: HandEye = HandEye(),
    rgb_depth_x_correction_m: float = -0.007,
    approach_offset_base_m=(0.0, 0.0, 0.0),
) -> PixelToBaseDebug:
    p_cam = depth_pixel_to_camera(pixel_xy, depth_m, intr)
    p_cam[0] += float(rgb_depth_x_correction_m)
    p_arm_cam_axes = d435_point_to_arm_camera_axes(p_cam)
    T_ee_target = hand_eye.matrix() @ euler_xyz_to_matrix(p_arm_cam_axes)
    T_base_target = np.asarray(T_base_ee, dtype=float) @ T_ee_target
    p = T_base_target[:3, 3].copy()
    p += np.array(approach_offset_base_m, dtype=float)
    return PixelToBaseDebug(
        pixel_xy=(float(pixel_xy[0]), float(pixel_xy[1])),
        depth_m=float(depth_m),
        point_camera_m=tuple(float(v) for v in p_cam),
        point_arm_camera_axes_m=tuple(float(v) for v in p_arm_cam_axes),
        point_base_m=tuple(float(v) for v in p),
    )


def target_pixel_to_base_point(
    pixel_xy: Tuple[float, float],
    depth_m: float,
    intr: CameraIntrinsics,
    T_base_ee: np.ndarray,
    hand_eye: HandEye = HandEye(),
    rgb_depth_x_correction_m: float = -0.007,
    approach_offset_base_m=(0.0, 0.0, 0.0),
) -> np.ndarray:
    """Pixel+depth -> arm base 3D point.

    This mirrors dynamic_space_grab.py: pixel/depth to camera, small x correction,
    axis remap, hand-to-camera transform, then base/end-effector transform.
    """
    dbg = target_pixel_to_base_point_debug(
        pixel_xy, depth_m, intr, T_base_ee, hand_eye, rgb_depth_x_correction_m, approach_offset_base_m
    )
    return np.array(dbg.point_base_m, dtype=float)
