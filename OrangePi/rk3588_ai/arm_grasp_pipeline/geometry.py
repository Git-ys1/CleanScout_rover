# coding: utf-8
"""Geometry primitives for the dynamic wrist-camera/TCP frame chain.

All vectors are column vectors.  A matrix named ``T_parent_child`` converts a
point expressed in ``child`` into ``parent``.  The live grasp path therefore
uses::

    T_base_camera = T_base_wrist(q0..q3) @ T_wrist_camera
    T_base_tcp    = T_base_wrist(q0..q3) @ T_wrist_tcp

Servo004 and Servo005 are deliberately absent from the camera chain.  Legacy
pixel/tool helpers remain at the bottom of this module for the explicitly
deprecated fixed-view path.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
from typing import Dict, Iterable, Mapping, Optional, Sequence, Tuple

import numpy as np


BASE_CONVENTION = "x_forward_y_left_z_up"
CAMERA_CONVENTION = "realsense_color_optical_x_right_y_down_z_forward"
WRIST_FRAME_NAMES = ("servo004_stator", "servo004_stator_housing")


@dataclass(frozen=True)
class CameraIntrinsics:
    fx: float
    fy: float
    cx: float
    cy: float


@dataclass(frozen=True)
class HandEye:
    """Legacy-compatible ``T_tool_camera`` representation.

    New dynamic code should load :class:`FrameTransforms` and use
    ``T_wrist_camera_color_optical``.  This class is retained so the historical
    fixed-view diagnostics keep working.
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
            return validate_rigid_transform(
                self.matrix_4x4, "T_tool_camera_color_optical"
            )
        return euler_xyz_to_matrix(
            (self.x, self.y, self.z),
            (self.roll_deg, self.pitch_deg, self.yaw_deg),
        )


@dataclass(frozen=True)
class PixelToBaseDebug:
    pixel_xy: Tuple[float, float]
    depth_m: float
    point_camera_m: Tuple[float, float, float]
    point_tool_m: Tuple[float, float, float]
    point_base_m: Tuple[float, float, float]


def _vector(values: Iterable[float], length: int, name: str) -> np.ndarray:
    result = np.asarray(list(values), dtype=float)
    if result.shape != (length,) or not np.all(np.isfinite(result)):
        raise ValueError("{} must contain {} finite values".format(name, length))
    return result


def matrix_from_translation_rotation(
    xyz: Iterable[float], R: Optional[np.ndarray] = None
) -> np.ndarray:
    translation = _vector(xyz, 3, "xyz")
    matrix = np.eye(4, dtype=float)
    if R is not None:
        rotation = np.asarray(R, dtype=float)
        if rotation.shape != (3, 3) or not np.all(np.isfinite(rotation)):
            raise ValueError("R must be a finite 3x3 matrix")
        matrix[:3, :3] = rotation
    matrix[:3, 3] = translation
    return matrix


def validate_rigid_transform(
    matrix,
    name: str = "transform",
    max_translation_m: Optional[float] = None,
) -> np.ndarray:
    """Return a checked copy of a 4x4 proper rigid transform."""

    transform = np.asarray(matrix, dtype=float)
    if transform.shape != (4, 4) or not np.all(np.isfinite(transform)):
        raise ValueError("{} must be a finite 4x4 matrix".format(name))
    if not np.allclose(transform[3], (0.0, 0.0, 0.0, 1.0), atol=1e-9):
        raise ValueError("{} must end with [0, 0, 0, 1]".format(name))
    rotation = transform[:3, :3]
    if not np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-6):
        raise ValueError("{} rotation must be orthonormal".format(name))
    if not np.isclose(np.linalg.det(rotation), 1.0, atol=1e-6):
        raise ValueError("{} rotation determinant must be +1".format(name))
    if max_translation_m is not None:
        limit = float(max_translation_m)
        if not math.isfinite(limit) or limit <= 0.0:
            raise ValueError("max_translation_m must be positive and finite")
        if float(np.linalg.norm(transform[:3, 3])) > limit:
            raise ValueError(
                "{} translation exceeds {} m; check units".format(name, limit)
            )
    return transform.copy()


def euler_xyz_to_matrix(
    xyz: Iterable[float], euler_deg: Iterable[float] = (0.0, 0.0, 0.0)
) -> np.ndarray:
    """Build a transform using fixed-parent ``Rz @ Ry @ Rx`` rotation order."""

    translation = _vector(xyz, 3, "xyz")
    roll, pitch, yaw = [math.radians(value) for value in _vector(
        euler_deg, 3, "euler_deg"
    )]
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]], dtype=float)
    ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]], dtype=float)
    rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]], dtype=float)
    return matrix_from_translation_rotation(translation, rz @ ry @ rx)


def axis_mapping_to_rotation(axis_mapping) -> np.ndarray:
    """Convert a child-axis mapping into ``R_parent_child``.

    ``"-y,-z,+x"`` means child +X points along parent -Y, child +Y points
    along parent -Z, and child +Z points along parent +X.  The three mapped
    axes become the columns of the returned rotation matrix.
    """

    if isinstance(axis_mapping, str):
        tokens = [token.strip().lower() for token in axis_mapping.split(",")]
    else:
        tokens = [str(token).strip().lower() for token in axis_mapping]
    if len(tokens) != 3:
        raise ValueError("axis mapping must contain child x,y,z mappings")
    basis = {
        "+x": np.array([1.0, 0.0, 0.0]),
        "x": np.array([1.0, 0.0, 0.0]),
        "-x": np.array([-1.0, 0.0, 0.0]),
        "+y": np.array([0.0, 1.0, 0.0]),
        "y": np.array([0.0, 1.0, 0.0]),
        "-y": np.array([0.0, -1.0, 0.0]),
        "+z": np.array([0.0, 0.0, 1.0]),
        "z": np.array([0.0, 0.0, 1.0]),
        "-z": np.array([0.0, 0.0, -1.0]),
    }
    try:
        rotation = np.column_stack([basis[token] for token in tokens])
    except KeyError as exc:
        raise ValueError("invalid axis mapping token: {}".format(exc.args[0]))
    checked = validate_rigid_transform(
        matrix_from_translation_rotation((0.0, 0.0, 0.0), rotation),
        "axis_mapping",
    )
    return checked[:3, :3]


def invert_transform(matrix: np.ndarray) -> np.ndarray:
    transform = validate_rigid_transform(matrix, "transform_to_invert")
    result = np.eye(4, dtype=float)
    rotation = transform[:3, :3]
    translation = transform[:3, 3]
    result[:3, :3] = rotation.T
    result[:3, 3] = -rotation.T @ translation
    return result


def compose_transforms(*matrices) -> np.ndarray:
    if not matrices:
        return np.eye(4, dtype=float)
    result = np.eye(4, dtype=float)
    for index, matrix in enumerate(matrices):
        result = result @ validate_rigid_transform(
            matrix, "transform_{}".format(index)
        )
    return validate_rigid_transform(result, "composed_transform")


def transform_point(matrix: np.ndarray, point_xyz: Iterable[float]) -> np.ndarray:
    transform = validate_rigid_transform(matrix, "point_transform")
    point = _vector(point_xyz, 3, "point_xyz")
    homogeneous = np.ones(4, dtype=float)
    homogeneous[:3] = point
    return (transform @ homogeneous)[:3]


def rotation_difference_deg(first, second) -> float:
    a = validate_rigid_transform(first, "first_transform")[:3, :3]
    b = validate_rigid_transform(second, "second_transform")[:3, :3]
    cosine = float(np.clip((np.trace(a.T @ b) - 1.0) * 0.5, -1.0, 1.0))
    return math.degrees(math.acos(cosine))


def transforms_consistent(
    first,
    second,
    translation_tolerance_m: float,
    rotation_tolerance_deg: float,
) -> bool:
    a = validate_rigid_transform(first, "first_transform")
    b = validate_rigid_transform(second, "second_transform")
    translation_error = float(np.linalg.norm(a[:3, 3] - b[:3, 3]))
    return (
        translation_error <= float(translation_tolerance_m)
        and rotation_difference_deg(a, b) <= float(rotation_tolerance_deg)
    )


def dynamic_base_camera(
    T_base_wrist: np.ndarray, T_wrist_camera: np.ndarray
) -> np.ndarray:
    """Pure dynamic camera chain; only the live wrist pose may vary."""

    return compose_transforms(T_base_wrist, T_wrist_camera)


def dynamic_base_tcp(
    T_base_wrist: np.ndarray, T_wrist_tcp: np.ndarray
) -> np.ndarray:
    return compose_transforms(T_base_wrist, T_wrist_tcp)


@dataclass(frozen=True)
class FrameTransforms:
    """Normalized runtime matrices and their calibration gates."""

    T_wrist_camera_color_optical: np.ndarray
    T_wrist_tcp_open: np.ndarray
    T_wrist_tcp_closed: np.ndarray
    servo004_fixed_pwm: int = 1500
    hand_eye_calibrated: bool = False
    open_calibrated: bool = False
    closed_calibrated: bool = False
    active_grasp_tcp: str = "closed"
    camera_parent: str = "servo004_stator"

    def __post_init__(self) -> None:
        for field_name in (
            "T_wrist_camera_color_optical",
            "T_wrist_tcp_open",
            "T_wrist_tcp_closed",
        ):
            checked = validate_rigid_transform(
                getattr(self, field_name), field_name, max_translation_m=2.0
            )
            checked.setflags(write=False)
            object.__setattr__(self, field_name, checked)
        if self.camera_parent not in WRIST_FRAME_NAMES:
            raise ValueError("camera_parent must be Servo004 stator")
        if int(self.servo004_fixed_pwm) != 1500:
            raise ValueError("dynamic grasp requires Servo004 fixed at PWM 1500")
        if self.active_grasp_tcp not in ("open", "closed"):
            raise ValueError("active_grasp_tcp must be 'open' or 'closed'")

    @classmethod
    def from_config(cls, config: Mapping, require_calibrated: bool = False):
        frames = config.get("frames")
        hand_eye = config.get("hand_eye")
        tool_tcp = config.get("tool_tcp")
        if not isinstance(frames, Mapping):
            raise ValueError("config.frames is required")
        if not isinstance(hand_eye, Mapping):
            raise ValueError("config.hand_eye is required")
        if not isinstance(tool_tcp, Mapping):
            raise ValueError("config.tool_tcp is required")
        if frames.get("base_convention") != BASE_CONVENTION:
            raise ValueError("unsupported base frame convention")
        if frames.get("camera_convention") != CAMERA_CONVENTION:
            raise ValueError("unsupported camera frame convention")

        camera_matrix = hand_eye.get("T_wrist_camera_color_optical")
        open_matrix = tool_tcp.get("T_wrist_tcp_open")
        closed_matrix = tool_tcp.get("T_wrist_tcp_closed")
        if camera_matrix is None:
            raise ValueError("hand_eye.T_wrist_camera_color_optical is not configured")
        if open_matrix is None or closed_matrix is None:
            raise ValueError("both open and closed wrist-to-TCP matrices are required")

        result = cls(
            T_wrist_camera_color_optical=camera_matrix,
            T_wrist_tcp_open=open_matrix,
            T_wrist_tcp_closed=closed_matrix,
            servo004_fixed_pwm=int(frames.get("servo004_fixed_pwm", -1)),
            hand_eye_calibrated=bool(hand_eye.get("calibrated", False)),
            open_calibrated=bool(tool_tcp.get("open_calibrated", False)),
            closed_calibrated=bool(tool_tcp.get("closed_calibrated", False)),
            active_grasp_tcp=str(tool_tcp.get("active_grasp_tcp", "closed")),
            camera_parent=str(frames.get("camera_parent", "")),
        )
        if require_calibrated:
            failures = []
            if not result.hand_eye_calibrated:
                failures.append("hand-eye")
            if result.active_grasp_tcp == "closed" and not result.closed_calibrated:
                failures.append("closed TCP")
            if result.active_grasp_tcp == "open" and not result.open_calibrated:
                failures.append("open TCP")
            if failures:
                raise ValueError(
                    "uncalibrated dynamic transforms: {}".format(", ".join(failures))
                )
        return result

    @property
    def T_wrist_camera(self) -> np.ndarray:
        return self.T_wrist_camera_color_optical.copy()

    def wrist_tcp(self, tcp_name: Optional[str] = None) -> np.ndarray:
        name = self.active_grasp_tcp if tcp_name is None else str(tcp_name)
        if name == "open":
            return self.T_wrist_tcp_open.copy()
        if name == "closed":
            return self.T_wrist_tcp_closed.copy()
        raise ValueError("tcp_name must be 'open' or 'closed'")

    def base_camera(self, T_base_wrist: np.ndarray) -> np.ndarray:
        return dynamic_base_camera(T_base_wrist, self.T_wrist_camera)

    def base_tcp(
        self, T_base_wrist: np.ndarray, tcp_name: Optional[str] = None
    ) -> np.ndarray:
        return dynamic_base_tcp(T_base_wrist, self.wrist_tcp(tcp_name))


def load_frame_transforms(config_or_path, require_calibrated: bool = False) -> FrameTransforms:
    if isinstance(config_or_path, Mapping):
        config = config_or_path
    elif isinstance(config_or_path, (str, bytes, os.PathLike, Path)):
        with Path(config_or_path).open("r", encoding="utf-8") as handle:
            config = json.load(handle)
    else:
        raise TypeError("config_or_path must be a mapping or JSON path")
    return FrameTransforms.from_config(config, require_calibrated=require_calibrated)


def dynamic_base_camera_from_pwm(kinematics, servo_pwms, frames: FrameTransforms):
    values = tuple(int(value) for value in servo_pwms)
    if len(values) < 4:
        raise ValueError("Servo000..003 PWM values are required")
    T_base_wrist = kinematics.forward_wrist_matrix_from_pwm(values[:4])
    return frames.base_camera(T_base_wrist)


def dynamic_base_tcp_from_pwm(
    kinematics, servo_pwms, frames: FrameTransforms, tcp_name: Optional[str] = None
):
    values = tuple(int(value) for value in servo_pwms)
    if len(values) < 4:
        raise ValueError("Servo000..003 PWM values are required")
    T_base_wrist = kinematics.forward_wrist_matrix_from_pwm(values[:4])
    return frames.base_tcp(T_base_wrist, tcp_name)


@dataclass(frozen=True)
class EnvironmentGeometry:
    base_mounting_plane_to_table_m: float
    table_surface_z_base_m: float

    @classmethod
    def from_config(cls, config: Mapping):
        environment = config.get("environment")
        if not isinstance(environment, Mapping):
            raise ValueError("config.environment is required")
        distance = float(environment.get("base_mounting_plane_to_table_m", 0.0))
        table_z = float(environment.get("table_surface_z_base_m", float("nan")))
        if not math.isfinite(distance) or distance <= 0.0:
            raise ValueError(
                "environment.base_mounting_plane_to_table_m must be positive metres"
            )
        if not math.isfinite(table_z):
            raise ValueError("environment.table_surface_z_base_m must be finite metres")
        if not math.isclose(table_z, -distance, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError(
                "with base +Z up, table_surface_z_base_m must equal the negative "
                "base-to-table distance"
            )
        return cls(distance, table_z)


def load_environment_geometry(config_or_path) -> EnvironmentGeometry:
    if isinstance(config_or_path, Mapping):
        config = config_or_path
    else:
        with Path(config_or_path).open("r", encoding="utf-8") as handle:
            config = json.load(handle)
    return EnvironmentGeometry.from_config(config)


def _unit_vector(vector: Iterable[float], name: str) -> np.ndarray:
    value = _vector(vector, 3, name)
    norm = float(np.linalg.norm(value))
    if norm <= 1e-12:
        raise ValueError("{} must not be zero".format(name))
    return value / norm


def approach_frame_matrix(
    origin_base_m: Iterable[float],
    along_base: Iterable[float],
    vertical_hint_base: Iterable[float] = (0.0, 0.0, 1.0),
) -> np.ndarray:
    """Return ``T_base_approach`` with columns along/lateral/vertical."""

    along = _unit_vector(along_base, "along_base")
    vertical_hint = _unit_vector(vertical_hint_base, "vertical_hint_base")
    lateral = np.cross(vertical_hint, along)
    if float(np.linalg.norm(lateral)) <= 1e-9:
        fallback = np.array([0.0, 1.0, 0.0], dtype=float)
        lateral = np.cross(fallback, along)
    lateral = _unit_vector(lateral, "lateral_axis")
    vertical = _unit_vector(np.cross(along, lateral), "vertical_axis")
    rotation = np.column_stack((along, lateral, vertical))
    return validate_rigid_transform(
        matrix_from_translation_rotation(origin_base_m, rotation),
        "T_base_approach",
    )


def apply_target_pixel_offset(
    raw_pixel_xy: Iterable[float], target_pixel_offset_px: Iterable[float]
) -> Tuple[float, float]:
    raw = _vector(raw_pixel_xy, 2, "raw_pixel_xy")
    offset = _vector(target_pixel_offset_px, 2, "target_pixel_offset_px")
    selected = raw + offset
    return float(selected[0]), float(selected[1])


@dataclass(frozen=True)
class GraspCompensationResult:
    raw_point_camera: Tuple[float, float, float]
    corrected_point_camera: Tuple[float, float, float]
    raw_point_base_surface: Tuple[float, float, float]
    object_center_point: Tuple[float, float, float]
    local_approach_frame: np.ndarray
    applied_compensation: Mapping[str, object]
    final_grasp_point_base: Tuple[float, float, float]


def apply_grasp_compensation(
    raw_point_camera_m: Iterable[float],
    T_base_camera: np.ndarray,
    compensation: Mapping,
    approach_direction_base: Optional[Iterable[float]] = None,
) -> GraspCompensationResult:
    """Apply the configured physical correction stack in the mandated order.

    No distance default is embedded here.  Every scalar/vector is required
    from configuration, and all intermediate values are returned for JSONL
    logging.
    """

    required = {
        "target_pixel_offset_px",
        "depth_bias_m",
        "camera_point_bias_m",
        "object_surface_to_grasp_center_m",
        "object_center_axis",
        "motion_approach_axis",
        "grasp_bias_approach_frame_m",
        "final_insertion_m",
        "pregrasp_standoff_m",
        "approach_step_m",
        "max_approach_step_m",
        "close_distance_m",
        "grasp_height_offset_m",
    }
    missing = sorted(required.difference(compensation))
    if missing:
        raise ValueError(
            "grasp_compensation missing fields: {}".format(", ".join(missing))
        )

    raw_camera = _vector(raw_point_camera_m, 3, "raw_point_camera_m")
    if raw_camera[2] <= 0.0:
        raise ValueError("raw camera depth must be positive")
    depth_bias = float(compensation["depth_bias_m"])
    if not math.isfinite(depth_bias) or raw_camera[2] + depth_bias <= 0.0:
        raise ValueError("depth_bias_m produces an invalid depth")

    # RealSense deprojection uses optical Z as depth.  Scaling the complete
    # point preserves the selected pixel ray when that depth is corrected.
    corrected_camera = raw_camera * ((raw_camera[2] + depth_bias) / raw_camera[2])
    camera_bias = _vector(
        compensation["camera_point_bias_m"], 3, "camera_point_bias_m"
    )
    corrected_camera = corrected_camera + camera_bias

    base_camera = validate_rigid_transform(T_base_camera, "T_base_camera")
    surface_base = transform_point(base_camera, corrected_camera)

    center_distance = float(compensation["object_surface_to_grasp_center_m"])
    if not math.isfinite(center_distance) or center_distance < 0.0:
        raise ValueError("object_surface_to_grasp_center_m must be non-negative")
    axis_mode = str(compensation["object_center_axis"])
    camera_ray_base = _unit_vector(
        base_camera[:3, :3] @ corrected_camera, "camera_ray_base"
    )
    if axis_mode == "camera_ray":
        center_axis = camera_ray_base
    elif axis_mode == "approach_axis":
        if approach_direction_base is None:
            raise ValueError("approach_axis requires approach_direction_base")
        center_axis = _unit_vector(
            approach_direction_base, "approach_direction_base"
        )
    else:
        raise ValueError("object_center_axis must be camera_ray or approach_axis")
    object_center = surface_base + center_axis * center_distance

    if approach_direction_base is not None:
        along = _unit_vector(approach_direction_base, "approach_direction_base")
    else:
        motion_axis_mode = str(compensation["motion_approach_axis"])
        if motion_axis_mode == "camera_ray":
            along = center_axis
        elif motion_axis_mode == "base_horizontal_radial":
            along = np.asarray(object_center, dtype=float).copy()
            along[2] = 0.0
            along = _unit_vector(along, "base_horizontal_radial")
        else:
            raise ValueError(
                "motion_approach_axis must be camera_ray or base_horizontal_radial"
            )
    local_frame = approach_frame_matrix(object_center, along)

    local_bias = _vector(
        compensation["grasp_bias_approach_frame_m"],
        3,
        "grasp_bias_approach_frame_m",
    )
    height_offset = float(compensation["grasp_height_offset_m"])
    final_insertion = float(compensation["final_insertion_m"])
    if not math.isfinite(height_offset) or not math.isfinite(final_insertion):
        raise ValueError("height and insertion compensation must be finite")
    local_total = local_bias.copy()
    local_total[0] += final_insertion
    local_total[2] += height_offset
    final_base = object_center + local_frame[:3, :3] @ local_total

    applied: Dict[str, object] = {
        "depth_bias_m": depth_bias,
        "camera_point_bias_m": tuple(float(value) for value in camera_bias),
        "object_surface_to_grasp_center_m": center_distance,
        "object_center_axis": axis_mode,
        "object_center_axis_base": tuple(float(value) for value in center_axis),
        "motion_approach_axis": str(compensation["motion_approach_axis"]),
        "motion_approach_axis_base": tuple(float(value) for value in along),
        "grasp_bias_approach_frame_m": tuple(float(value) for value in local_bias),
        "grasp_height_offset_m": height_offset,
        "final_insertion_m": final_insertion,
        "target_pixel_offset_px": tuple(
            float(value) for value in _vector(
                compensation["target_pixel_offset_px"],
                2,
                "target_pixel_offset_px",
            )
        ),
    }
    return GraspCompensationResult(
        raw_point_camera=tuple(float(value) for value in raw_camera),
        corrected_point_camera=tuple(float(value) for value in corrected_camera),
        raw_point_base_surface=tuple(float(value) for value in surface_base),
        object_center_point=tuple(float(value) for value in object_center),
        local_approach_frame=local_frame,
        applied_compensation=applied,
        final_grasp_point_base=tuple(float(value) for value in final_base),
    )


def depth_pixel_to_camera(
    pixel_xy: Tuple[float, float], depth_m: float, intr: CameraIntrinsics
) -> np.ndarray:
    u, v = pixel_xy
    z = float(depth_m)
    if not math.isfinite(z) or z <= 0.0:
        raise ValueError("depth_m must be positive and finite")
    if not all(math.isfinite(value) for value in (intr.fx, intr.fy, intr.cx, intr.cy)):
        raise ValueError("camera intrinsics must be finite")
    if intr.fx == 0.0 or intr.fy == 0.0:
        raise ValueError("camera focal lengths must be non-zero")
    x = (float(u) - intr.cx) * z / intr.fx
    y = (float(v) - intr.cy) * z / intr.fy
    return np.array([x, y, z], dtype=float)


def target_pixel_to_base_point_debug(
    pixel_xy: Tuple[float, float],
    depth_m: float,
    intr: CameraIntrinsics,
    T_base_tool: np.ndarray,
    hand_eye: HandEye = HandEye(),
    rgb_depth_x_correction_m: float = 0.0,
    approach_offset_base_m=(0.0, 0.0, 0.0),
) -> PixelToBaseDebug:
    """Legacy fixed-view helper retained for diagnostics and rollback."""

    point_camera = depth_pixel_to_camera(pixel_xy, depth_m, intr)
    point_camera[0] += float(rgb_depth_x_correction_m)
    point_tool = transform_point(hand_eye.matrix(), point_camera)
    point_base = transform_point(T_base_tool, point_tool)
    point_base += _vector(approach_offset_base_m, 3, "approach_offset_base_m")
    return PixelToBaseDebug(
        pixel_xy=(float(pixel_xy[0]), float(pixel_xy[1])),
        depth_m=float(depth_m),
        point_camera_m=tuple(float(value) for value in point_camera),
        point_tool_m=tuple(float(value) for value in point_tool),
        point_base_m=tuple(float(value) for value in point_base),
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
    debug = target_pixel_to_base_point_debug(
        pixel_xy,
        depth_m,
        intr,
        T_base_tool,
        hand_eye,
        rgb_depth_x_correction_m,
        approach_offset_base_m,
    )
    return np.array(debug.point_base_m, dtype=float)
