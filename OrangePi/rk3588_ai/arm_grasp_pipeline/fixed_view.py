# coding: utf-8
"""Fixed-view RGB-D calibration and target geometry.

The only transform used by this mode is ``T_base_camera_reference``::

    p_base = T_base_camera_reference @ p_camera

It is valid only while the arm is at the configured reference servo pose.
No PWM-derived forward-kinematics estimate participates in this transform.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Optional, Sequence, Tuple

import numpy as np

from .geometry import CameraIntrinsics, depth_pixel_to_camera, transform_point, validate_rigid_transform


DEFAULT_MAX_RMSE_M = 0.010
DEFAULT_MAX_POINT_ERROR_M = 0.015
REQUIRED_WRIST_PWM = 1500
CALIBRATION_CSV_FIELDS = (
    "camera_x", "camera_y", "camera_z",
    "base_x", "base_y", "base_z",
)


@dataclass(frozen=True)
class RigidCalibrationResult:
    matrix_4x4: np.ndarray
    errors_m: np.ndarray
    mean_error_m: float
    max_error_m: float
    rmse_m: float
    determinant: float

    def as_dict(self, max_rmse_m=DEFAULT_MAX_RMSE_M,
                max_point_error_m=DEFAULT_MAX_POINT_ERROR_M):
        quality_pass = (
            self.rmse_m <= float(max_rmse_m)
            and self.max_error_m <= float(max_point_error_m)
        )
        return {
            "T_base_camera_reference": self.matrix_4x4.tolist(),
            "base_to_camera_matrix_4x4": self.matrix_4x4.tolist(),
            "errors_m": [float(value) for value in self.errors_m],
            "mean_error_m": float(self.mean_error_m),
            "max_error_m": float(self.max_error_m),
            "rmse_m": float(self.rmse_m),
            "determinant": float(self.determinant),
            "quality_pass": bool(quality_pass),
        }


def solve_rigid_transform(camera_points_m, base_points_m) -> RigidCalibrationResult:
    """Solve unscaled Kabsch/Umeyama registration from camera to arm base."""
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
        raise ValueError("camera calibration points are degenerate or collinear")
    if np.linalg.matrix_rank(base_centered, tol=1e-9) < 2:
        raise ValueError("base calibration points are degenerate or collinear")

    covariance = camera_centered.T @ base_centered
    u, _, vt = np.linalg.svd(covariance)
    rotation = vt.T @ u.T
    determinant = float(np.linalg.det(rotation))
    if determinant < 0.0:
        raise ValueError("calibration correspondences imply a reflection")
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


def median_depth_around_pixel(depth_frames_m, pixel_xy, radius_px=4,
                              min_valid_samples=12) -> Optional[float]:
    """Return robust aligned depth around a clicked RGB pixel."""
    frames = np.asarray(depth_frames_m, dtype=float)
    if frames.ndim == 2:
        frames = frames[np.newaxis, ...]
    if frames.ndim != 3 or frames.shape[0] < 1:
        raise ValueError("depth_frames_m must be one depth image or a stack of images")
    radius = int(radius_px)
    if radius < 1:
        raise ValueError("radius_px must be at least 1")
    u = int(round(float(pixel_xy[0])))
    v = int(round(float(pixel_xy[1])))
    height, width = frames.shape[1:]
    if u < 0 or u >= width or v < 0 or v >= height:
        raise ValueError("clicked pixel is outside the depth image")
    x1, x2 = max(0, u - radius), min(width, u + radius + 1)
    y1, y2 = max(0, v - radius), min(height, v + radius + 1)
    values = frames[:, y1:y2, x1:x2].reshape(-1)
    values = values[np.isfinite(values)]
    values = values[values > 0.0]
    if values.size < int(min_valid_samples):
        return None
    low, high = np.percentile(values, [15, 85])
    trimmed = values[(values >= low) & (values <= high)]
    if trimmed.size < int(min_valid_samples):
        trimmed = values
    return float(np.median(trimmed))


@dataclass(frozen=True)
class FixedViewCalibration:
    calibrated: bool
    reference_servo_pwms: Tuple[int, int, int, int, int, int]
    base_to_camera_matrix_4x4: Optional[Sequence[Sequence[float]]]
    rmse_m: Optional[float]
    max_error_m: Optional[float]
    max_rmse_m: float = DEFAULT_MAX_RMSE_M
    max_point_error_m: float = DEFAULT_MAX_POINT_ERROR_M

    @classmethod
    def from_mapping(cls, mapping: Mapping):
        required = {
            "calibrated", "reference_servo_pwms", "base_to_camera_matrix_4x4",
            "rmse_m", "max_error_m", "max_rmse_m", "max_point_error_m",
        }
        missing = sorted(required.difference(mapping))
        if missing:
            raise ValueError(
                "fixed_view_calibration missing config fields: " + ", ".join(missing)
            )
        if not isinstance(mapping["calibrated"], bool):
            raise ValueError("fixed_view_calibration.calibrated must be a boolean")
        reference = tuple(int(value) for value in mapping["reference_servo_pwms"])
        if len(reference) != 6:
            raise ValueError("fixed_view_calibration.reference_servo_pwms must contain six values")
        return cls(
            calibrated=mapping["calibrated"],
            reference_servo_pwms=reference,
            base_to_camera_matrix_4x4=mapping["base_to_camera_matrix_4x4"],
            rmse_m=None if mapping["rmse_m"] is None else float(mapping["rmse_m"]),
            max_error_m=(
                None if mapping["max_error_m"] is None else float(mapping["max_error_m"])
            ),
            max_rmse_m=float(mapping["max_rmse_m"]),
            max_point_error_m=float(mapping["max_point_error_m"]),
        )

    def matrix(self) -> np.ndarray:
        if self.base_to_camera_matrix_4x4 is None:
            raise ValueError("fixed-view base_to_camera_matrix_4x4 is not configured")
        return validate_rigid_transform(
            self.base_to_camera_matrix_4x4,
            "T_base_camera_reference",
        )

    def readiness_errors(self, required_wrist_pwm=REQUIRED_WRIST_PWM):
        errors = []
        rmse_limit_valid = math.isfinite(self.max_rmse_m) and self.max_rmse_m > 0.0
        point_limit_valid = (
            math.isfinite(self.max_point_error_m) and self.max_point_error_m > 0.0
        )
        effective_rmse_limit = (
            min(self.max_rmse_m, DEFAULT_MAX_RMSE_M)
            if rmse_limit_valid else DEFAULT_MAX_RMSE_M
        )
        effective_point_limit = (
            min(self.max_point_error_m, DEFAULT_MAX_POINT_ERROR_M)
            if point_limit_valid else DEFAULT_MAX_POINT_ERROR_M
        )
        if not rmse_limit_valid:
            errors.append("fixed-view max_rmse_m must be positive and finite")
        elif self.max_rmse_m > DEFAULT_MAX_RMSE_M:
            errors.append("fixed-view max_rmse_m may not exceed 0.010 m")
        if not point_limit_valid:
            errors.append("fixed-view max_point_error_m must be positive and finite")
        elif self.max_point_error_m > DEFAULT_MAX_POINT_ERROR_M:
            errors.append("fixed-view max_point_error_m may not exceed 0.015 m")
        if not self.calibrated:
            errors.append("fixed_view_calibration.calibrated is false")
        try:
            self.matrix()
        except ValueError as exc:
            errors.append(str(exc))
        if self.rmse_m is None or not math.isfinite(self.rmse_m) or self.rmse_m < 0.0:
            errors.append("fixed-view rmse_m is missing or non-finite")
        elif self.rmse_m > effective_rmse_limit:
            errors.append("fixed-view rmse_m exceeds {:.3f} m".format(effective_rmse_limit))
        if (self.max_error_m is None or not math.isfinite(self.max_error_m)
                or self.max_error_m < 0.0):
            errors.append("fixed-view max_error_m is missing or non-finite")
        elif self.max_error_m > effective_point_limit:
            errors.append("fixed-view max_error_m exceeds {:.3f} m".format(
                effective_point_limit
            ))
        if any(value < 500 or value > 2500 for value in self.reference_servo_pwms):
            errors.append("fixed-view reference servo PWM is outside 500..2500")
        if self.reference_servo_pwms[4] != int(required_wrist_pwm):
            errors.append("Servo004 reference PWM must be {}".format(required_wrist_pwm))
        return errors

    def require_real_grasp_ready(self, required_wrist_pwm=REQUIRED_WRIST_PWM):
        errors = self.readiness_errors(required_wrist_pwm)
        if errors:
            raise ValueError("fixed-view real grasp rejected: " + "; ".join(errors))


@dataclass(frozen=True)
class ObjectGeometry:
    bottle_radius_m: float = 0.032
    grasp_height_offset_m: float = 0.0

    @classmethod
    def from_mapping(cls, mapping: Mapping):
        required = {"bottle_radius_m", "grasp_height_offset_m"}
        missing = sorted(required.difference(mapping))
        if missing:
            raise ValueError("object_geometry missing config fields: " + ", ".join(missing))
        result = cls(
            bottle_radius_m=float(mapping["bottle_radius_m"]),
            grasp_height_offset_m=float(mapping["grasp_height_offset_m"]),
        )
        if not math.isfinite(result.bottle_radius_m) or result.bottle_radius_m <= 0.0:
            raise ValueError("object_geometry.bottle_radius_m must be positive and finite")
        if not math.isfinite(result.grasp_height_offset_m):
            raise ValueError("object_geometry.grasp_height_offset_m must be finite")
        return result


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


def fixed_view_target_debug(pixel_xy, depth_m, intrinsics: CameraIntrinsics,
                            T_base_camera_reference,
                            object_geometry: ObjectGeometry) -> FixedViewTargetDebug:
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


def pre_grasp_from_bottle_center(bottle_center_base_m, standoff_m) -> np.ndarray:
    standoff = float(standoff_m)
    if not math.isfinite(standoff) or standoff <= 0.0:
        raise ValueError("pre-grasp standoff must be positive and finite")
    center = np.asarray(bottle_center_base_m, dtype=float)
    return center - horizontal_approach_axis(center) * standoff


def cartesian_line_points(start_xyz_m, end_xyz_m, max_spacing_m):
    """Return an endpoint-inclusive Cartesian line excluding the start point."""
    start = np.asarray(start_xyz_m, dtype=float)
    end = np.asarray(end_xyz_m, dtype=float)
    spacing = float(max_spacing_m)
    if start.shape != (3,) or end.shape != (3,) or not np.all(np.isfinite([start, end])):
        raise ValueError("Cartesian line endpoints must be finite XYZ values")
    if not math.isfinite(spacing) or spacing <= 0.0:
        raise ValueError("Cartesian waypoint spacing must be positive and finite")
    distance = float(np.linalg.norm(end - start))
    if distance <= 1e-12:
        return [end.copy()]
    count = max(1, int(math.ceil(distance / spacing)))
    return [start + (end - start) * (float(index) / count) for index in range(1, count + 1)]
