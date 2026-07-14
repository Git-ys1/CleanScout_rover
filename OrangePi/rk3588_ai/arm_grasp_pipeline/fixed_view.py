# coding: utf-8
"""Fixed-view camera calibration and bottle target geometry.

The fixed observation mode uses one calibrated transform directly from the
RealSense color optical frame to the arm base frame::

    p_base = T_base_camera_reference @ p_camera

No live joint/PWM estimate participates in this transform.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Optional, Sequence, Tuple

import numpy as np

from .geometry import CameraIntrinsics, depth_pixel_to_camera, transform_point, validate_rigid_transform


MAX_FIXED_VIEW_RMSE_M = 0.010
MAX_FIXED_VIEW_ERROR_M = 0.015


@dataclass(frozen=True)
class RigidCalibrationResult:
    matrix_4x4: np.ndarray
    errors_m: np.ndarray
    mean_error_m: float
    max_error_m: float
    rmse_m: float
    determinant: float

    def as_dict(self):
        return {
            "base_to_camera_matrix_4x4": self.matrix_4x4.tolist(),
            "errors_m": [float(value) for value in self.errors_m],
            "mean_error_m": float(self.mean_error_m),
            "max_error_m": float(self.max_error_m),
            "rmse_m": float(self.rmse_m),
            "determinant": float(self.determinant),
            "quality_pass": bool(
                self.rmse_m <= MAX_FIXED_VIEW_RMSE_M
                and self.max_error_m <= MAX_FIXED_VIEW_ERROR_M
            ),
        }


def solve_rigid_transform(camera_points_m, base_points_m) -> RigidCalibrationResult:
    """Recover ``T_base_camera`` with an unscaled SVD/Umeyama fit."""
    camera = np.asarray(camera_points_m, dtype=float)
    base = np.asarray(base_points_m, dtype=float)
    if camera.shape != base.shape or camera.ndim != 2 or camera.shape[1] != 3:
        raise ValueError("camera/base calibration points must be matching Nx3 arrays")
    if camera.shape[0] < 3:
        raise ValueError("at least three calibration correspondences are required")
    if not np.all(np.isfinite(camera)) or not np.all(np.isfinite(base)):
        raise ValueError("calibration points must be finite")

    camera_mean = np.mean(camera, axis=0)
    base_mean = np.mean(base, axis=0)
    camera_centered = camera - camera_mean
    base_centered = base - base_mean
    if np.linalg.matrix_rank(camera_centered, tol=1e-9) < 2:
        raise ValueError("camera calibration points are degenerate/collinear")
    if np.linalg.matrix_rank(base_centered, tol=1e-9) < 2:
        raise ValueError("base calibration points are degenerate/collinear")

    covariance = camera_centered.T @ base_centered
    u, _, vt = np.linalg.svd(covariance)
    rotation = vt.T @ u.T
    determinant = float(np.linalg.det(rotation))
    if determinant < 0.0:
        raise ValueError("calibration correspondences imply a reflection; check point pairing/axes")
    if not math.isclose(determinant, 1.0, rel_tol=0.0, abs_tol=1e-6):
        raise ValueError("calibration rotation determinant is not close to +1")

    translation = base_mean - rotation @ camera_mean
    matrix = np.eye(4, dtype=float)
    matrix[:3, :3] = rotation
    matrix[:3, 3] = translation
    matrix = validate_rigid_transform(matrix, "T_base_camera_reference")

    predicted = (rotation @ camera.T).T + translation
    errors = np.linalg.norm(predicted - base, axis=1)
    return RigidCalibrationResult(
        matrix_4x4=matrix,
        errors_m=errors,
        mean_error_m=float(np.mean(errors)),
        max_error_m=float(np.max(errors)),
        rmse_m=float(np.sqrt(np.mean(np.square(errors)))),
        determinant=determinant,
    )


@dataclass(frozen=True)
class FixedViewCalibration:
    calibrated: bool
    reference_servo_pwms: Tuple[int, int, int, int, int, int]
    base_to_camera_matrix_4x4: Optional[Sequence[Sequence[float]]]
    rmse_m: Optional[float]
    max_error_m: Optional[float]

    @classmethod
    def from_mapping(cls, mapping: Mapping):
        reference = tuple(int(value) for value in mapping.get(
            "reference_servo_pwms", (1380, 1909, 1900, 620, 1500, 1500)
        ))
        if len(reference) != 6:
            raise ValueError("fixed_view_calibration.reference_servo_pwms must contain six values")
        return cls(
            calibrated=bool(mapping.get("calibrated", False)),
            reference_servo_pwms=reference,
            base_to_camera_matrix_4x4=mapping.get("base_to_camera_matrix_4x4"),
            rmse_m=None if mapping.get("rmse_m") is None else float(mapping["rmse_m"]),
            max_error_m=(
                None if mapping.get("max_error_m") is None else float(mapping["max_error_m"])
            ),
        )

    def matrix(self) -> np.ndarray:
        if self.base_to_camera_matrix_4x4 is None:
            raise ValueError("fixed-view base_to_camera_matrix_4x4 is not configured")
        return validate_rigid_transform(
            self.base_to_camera_matrix_4x4,
            "T_base_camera_reference",
        )

    def readiness_errors(self, required_wrist_pwm: int = 1500):
        errors = []
        if not self.calibrated:
            errors.append("fixed_view_calibration.calibrated is false")
        try:
            self.matrix()
        except ValueError as exc:
            errors.append(str(exc))
        if self.rmse_m is None or not math.isfinite(self.rmse_m):
            errors.append("fixed-view rmse_m is missing/non-finite")
        elif self.rmse_m > MAX_FIXED_VIEW_RMSE_M:
            errors.append("fixed-view rmse_m exceeds 0.010 m")
        if self.max_error_m is None or not math.isfinite(self.max_error_m):
            errors.append("fixed-view max_error_m is missing/non-finite")
        elif self.max_error_m > MAX_FIXED_VIEW_ERROR_M:
            errors.append("fixed-view max_error_m exceeds 0.015 m")
        if any(value < 500 or value > 2500 for value in self.reference_servo_pwms):
            errors.append("fixed-view reference servo PWM is outside 500..2500")
        if self.reference_servo_pwms[4] != int(required_wrist_pwm):
            errors.append("Servo004 reference PWM must be {}".format(int(required_wrist_pwm)))
        return errors

    def require_real_grasp_ready(self, required_wrist_pwm: int = 1500) -> None:
        errors = self.readiness_errors(required_wrist_pwm)
        if errors:
            raise ValueError("fixed-view real grasp rejected: " + "; ".join(errors))


@dataclass(frozen=True)
class ObjectGeometry:
    bottle_radius_m: float = 0.032
    grasp_height_offset_m: float = 0.0

    @classmethod
    def from_mapping(cls, mapping: Mapping):
        geometry = cls(
            bottle_radius_m=float(mapping.get("bottle_radius_m", 0.032)),
            grasp_height_offset_m=float(mapping.get("grasp_height_offset_m", 0.0)),
        )
        if not math.isfinite(geometry.bottle_radius_m) or geometry.bottle_radius_m <= 0.0:
            raise ValueError("object_geometry.bottle_radius_m must be positive and finite")
        if not math.isfinite(geometry.grasp_height_offset_m):
            raise ValueError("object_geometry.grasp_height_offset_m must be finite")
        return geometry


@dataclass(frozen=True)
class FixedViewTargetDebug:
    pixel_xy: Tuple[float, float]
    depth_m: float
    point_camera_m: Tuple[float, float, float]
    point_base_surface_m: Tuple[float, float, float]
    bottle_center_base_m: Tuple[float, float, float]
    approach_axis_base: Tuple[float, float, float]


def horizontal_approach_axis(point_base_m) -> np.ndarray:
    point = np.asarray(point_base_m, dtype=float)
    if point.shape != (3,) or not np.all(np.isfinite(point)):
        raise ValueError("base point must contain three finite values")
    radial = np.array([point[0], point[1], 0.0], dtype=float)
    length = float(np.linalg.norm(radial))
    if length <= 1e-9:
        raise ValueError("target lies on the base Z axis; horizontal approach is undefined")
    return radial / length


def fixed_view_target_debug(
    pixel_xy: Tuple[float, float],
    depth_m: float,
    intrinsics: CameraIntrinsics,
    T_base_camera_reference,
    object_geometry: ObjectGeometry,
) -> FixedViewTargetDebug:
    point_camera = depth_pixel_to_camera(pixel_xy, depth_m, intrinsics)
    matrix = validate_rigid_transform(T_base_camera_reference, "T_base_camera_reference")
    surface = transform_point(matrix, point_camera)
    approach_axis = horizontal_approach_axis(surface)
    center = surface + approach_axis * object_geometry.bottle_radius_m
    center[2] += object_geometry.grasp_height_offset_m
    return FixedViewTargetDebug(
        pixel_xy=(float(pixel_xy[0]), float(pixel_xy[1])),
        depth_m=float(depth_m),
        point_camera_m=tuple(float(value) for value in point_camera),
        point_base_surface_m=tuple(float(value) for value in surface),
        bottle_center_base_m=tuple(float(value) for value in center),
        approach_axis_base=tuple(float(value) for value in approach_axis),
    )


def pre_grasp_from_bottle_center(bottle_center_base_m, standoff_m: float) -> np.ndarray:
    standoff = float(standoff_m)
    if not math.isfinite(standoff) or standoff <= 0.0:
        raise ValueError("pre-grasp standoff must be positive and finite")
    center = np.asarray(bottle_center_base_m, dtype=float)
    return center - horizontal_approach_axis(center) * standoff
