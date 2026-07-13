# coding: utf-8
"""Camera projection and explicit base/tool/color-optical transforms.

Only the pixel-depth projection primitive is adapted from the ROS2 learning
package. CleanScout frame transforms are project-defined and require local
calibration; no reference-project axis swap or hand-eye seed is reused.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Optional, Sequence, Tuple

import numpy as np


@dataclass(frozen=True)
class CameraIntrinsics:
    fx: float
    fy: float
    cx: float
    cy: float


@dataclass(frozen=True)
class HandEye:
    """Rigid transform ``T_tool_camera`` in metres/degrees.

    D435 depth is aligned to color before deprojection, so camera points use
    the RealSense color optical frame: +X image-right, +Y image-down, +Z
    forward. The rotation below, not an extra hard-coded axis swap, maps that
    frame into the gripper TCP/tool frame.
    """
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    roll_deg: float = 0.0
    pitch_deg: float = 0.0
    yaw_deg: float = 0.0
    matrix_4x4: Optional[Sequence[Sequence[float]]] = None

    def matrix(self) -> np.ndarray:
        if self.matrix_4x4 is not None:
            return validate_rigid_transform(self.matrix_4x4, "T_tool_camera_color_optical")
        T = euler_xyz_to_matrix((self.x, self.y, self.z), (self.roll_deg, self.pitch_deg, self.yaw_deg))
        return T


@dataclass(frozen=True)
class PixelToBaseDebug:
    pixel_xy: Tuple[float, float]
    depth_m: float
    point_camera_m: Tuple[float, float, float]
    point_tool_m: Tuple[float, float, float]
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


def validate_rigid_transform(matrix, name: str = "transform") -> np.ndarray:
    T = np.asarray(matrix, dtype=float)
    if T.shape != (4, 4) or not np.all(np.isfinite(T)):
        raise ValueError("{} must be a finite 4x4 matrix".format(name))
    if not np.allclose(T[3], (0.0, 0.0, 0.0, 1.0), atol=1e-6):
        raise ValueError("{} must end with [0, 0, 0, 1]".format(name))
    R = T[:3, :3]
    if not np.allclose(R.T @ R, np.eye(3), atol=1e-4) or not np.isclose(np.linalg.det(R), 1.0, atol=1e-4):
        raise ValueError("{} rotation must be orthonormal with determinant +1".format(name))
    return T.copy()


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


def target_pixel_to_base_point_debug(
    pixel_xy: Tuple[float, float],
    depth_m: float,
    intr: CameraIntrinsics,
    T_base_tool: np.ndarray,
    hand_eye: HandEye = HandEye(),
    rgb_depth_x_correction_m: float = 0.0,
    approach_offset_base_m=(0.0, 0.0, 0.0),
) -> PixelToBaseDebug:
    p_cam = depth_pixel_to_camera(pixel_xy, depth_m, intr)
    p_cam[0] += float(rgb_depth_x_correction_m)
    p_tool = transform_point(hand_eye.matrix(), p_cam)
    p = transform_point(np.asarray(T_base_tool, dtype=float), p_tool)
    p += np.array(approach_offset_base_m, dtype=float)
    return PixelToBaseDebug(
        pixel_xy=(float(pixel_xy[0]), float(pixel_xy[1])),
        depth_m=float(depth_m),
        point_camera_m=tuple(float(v) for v in p_cam),
        point_tool_m=tuple(float(v) for v in p_tool),
        point_base_m=tuple(float(v) for v in p),
    )


def target_pixel_to_base_point(
    pixel_xy: Tuple[float, float],
    depth_m: float,
    intr: CameraIntrinsics,
    T_base_tool: np.ndarray,
    hand_eye: HandEye = HandEye(),
    rgb_depth_x_correction_m: float = 0.0,
    approach_offset_base_m=(0.0, 0.0, 0.0),
) -> np.ndarray:
    """Pixel+depth -> arm base 3D point.

    The point stays in the native RealSense optical frame until the calibrated
    ``T_tool_camera`` transform maps it into the tool frame.
    """
    dbg = target_pixel_to_base_point_debug(
        pixel_xy, depth_m, intr, T_base_tool, hand_eye, rgb_depth_x_correction_m, approach_offset_base_m
    )
    return np.array(dbg.point_base_m, dtype=float)
