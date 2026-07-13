#!/usr/bin/env python3
"""Regression checks for explicit base/tool/RealSense frame composition."""
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.geometry import (
    CameraIntrinsics,
    HandEye,
    euler_xyz_to_matrix,
    target_pixel_to_base_point_debug,
    validate_rigid_transform,
)


def main() -> int:
    intr = CameraIntrinsics(fx=600.0, fy=600.0, cx=320.0, cy=240.0)
    T_base_tool = euler_xyz_to_matrix((0.20, 0.03, 0.10))
    T_tool_camera = HandEye(x=0.01, y=-0.02, z=0.03)
    debug = target_pixel_to_base_point_debug(
        (320.0, 240.0),
        0.25,
        intr,
        T_base_tool,
        T_tool_camera,
        rgb_depth_x_correction_m=0.0,
    )
    assert np.allclose(debug.point_camera_m, (0.0, 0.0, 0.25))
    assert np.allclose(debug.point_tool_m, (0.01, -0.02, 0.28))
    assert np.allclose(debug.point_base_m, (0.21, 0.01, 0.38))

    rotated = target_pixel_to_base_point_debug(
        (320.0, 240.0),
        0.25,
        intr,
        np.eye(4),
        HandEye(yaw_deg=90.0),
    )
    assert np.allclose(rotated.point_base_m, (0.0, 0.0, 0.25), atol=1e-9)

    direct = HandEye(matrix_4x4=[
        [1.0, 0.0, 0.0, 0.01],
        [0.0, 1.0, 0.0, -0.02],
        [0.0, 0.0, 1.0, 0.03],
        [0.0, 0.0, 0.0, 1.0],
    ])
    assert np.allclose(direct.matrix(), T_tool_camera.matrix())
    try:
        validate_rigid_transform(np.diag([2.0, 1.0, 1.0, 1.0]), "bad")
    except ValueError as exc:
        assert "orthonormal" in str(exc)
    else:
        raise AssertionError("invalid rigid transform was accepted")
    print("GEOMETRY_FRAMES_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
