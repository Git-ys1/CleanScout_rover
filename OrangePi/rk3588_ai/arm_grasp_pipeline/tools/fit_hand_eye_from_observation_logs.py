#!/usr/bin/env python3
"""Fit wrist-to-camera rotation from static-target, multi-pose observe logs.

The measured translation is held fixed.  This tool never opens the serial port
and never writes configuration; it only prints a candidate and residuals for a
separate live-validation pass.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np


def _skew(v):
    x, y, z = (float(value) for value in v)
    return np.array([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]])


def _exp_so3(rotvec):
    value = np.asarray(rotvec, dtype=float)
    angle = float(np.linalg.norm(value))
    if angle < 1e-12:
        return np.eye(3) + _skew(value)
    axis = value / angle
    cross = _skew(axis)
    return np.eye(3) + math.sin(angle) * cross + (1.0 - math.cos(angle)) * (cross @ cross)


def _rotation_angle_deg(a, b):
    cosine = float(np.clip((np.trace(a.T @ b) - 1.0) * 0.5, -1.0, 1.0))
    return math.degrees(math.acos(cosine))


def _load_group(path, object_radius_m):
    samples = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            event = json.loads(line)
            if "T_base_wrist" not in event or "raw_point_camera" not in event:
                continue
            point = np.asarray(event["raw_point_camera"], dtype=float)
            norm = float(np.linalg.norm(point))
            if norm <= 0.0:
                continue
            # The RGB-D point is the visible bottle surface.  Shift along its
            # camera ray by the configured bottle radius before comparing
            # poses, so changing view direction does not compare two surfaces.
            center_camera = point + point / norm * float(object_radius_m)
            wrist = np.asarray(event["T_base_wrist"], dtype=float)
            samples.append((wrist[:3, :3], wrist[:3, 3], center_camera))
    if not samples:
        raise ValueError("no observation samples in {}".format(path))
    return samples


def _group_means(groups, rotation, translation):
    means = []
    for samples in groups:
        values = [base_r @ (rotation @ point + translation) + base_t for base_r, base_t, point in samples]
        means.append(np.mean(np.asarray(values), axis=0))
    return np.asarray(means)


def _residual(groups, rotation, translation):
    means = _group_means(groups, rotation, translation)
    common = np.mean(means, axis=0)
    return (means - common).reshape(-1)


def fit(
    groups,
    seed_rotation,
    translation,
    iterations=40,
    prior_weight=1e-3,
    max_change_deg=15.0,
):
    seed = np.asarray(seed_rotation, dtype=float).copy()
    delta_total = np.zeros(3, dtype=float)
    damping = 1e-5

    def objective(delta):
        spatial = _residual(groups, seed @ _exp_so3(delta), translation)
        if float(prior_weight) <= 0.0:
            return spatial
        return np.concatenate(
            (spatial, math.sqrt(float(prior_weight)) * np.asarray(delta))
        )

    max_change_rad = math.radians(float(max_change_deg))
    for _ in range(int(iterations)):
        residual = objective(delta_total)
        eps = 1e-5
        jacobian = np.empty((residual.size, 3), dtype=float)
        for axis in range(3):
            perturbed = delta_total.copy()
            perturbed[axis] += eps
            jacobian[:, axis] = (
                objective(perturbed) - residual
            ) / eps
        lhs = jacobian.T @ jacobian + damping * np.eye(3)
        rhs = -(jacobian.T @ residual)
        step = np.linalg.solve(lhs, rhs)
        if float(np.linalg.norm(step)) < 1e-10:
            break
        if float(np.linalg.norm(step)) > 0.15:
            step *= 0.15 / float(np.linalg.norm(step))
        candidate_delta = delta_total + step
        candidate_norm = float(np.linalg.norm(candidate_delta))
        if candidate_norm > max_change_rad:
            candidate_delta *= max_change_rad / candidate_norm
        if np.linalg.norm(objective(candidate_delta)) <= np.linalg.norm(residual):
            delta_total = candidate_delta
            damping = max(1e-9, damping * 0.5)
        else:
            damping = min(1.0, damping * 10.0)
    rotation = seed @ _exp_so3(delta_total)
    means = _group_means(groups, rotation, translation)
    pairwise = [
        float(np.linalg.norm(means[i] - means[j]))
        for i in range(len(means))
        for j in range(i + 1, len(means))
    ]
    return rotation, means, max(pairwise or [0.0]), _rotation_angle_deg(seed, rotation)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logs", nargs="+")
    parser.add_argument("--config", default="config/arm_grasp_default.json")
    parser.add_argument("--object-radius-m", type=float, default=None)
    parser.add_argument("--prior-weight", type=float, default=1e-3)
    parser.add_argument("--max-change-deg", type=float, default=15.0)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    matrix = np.asarray(config["hand_eye"]["T_wrist_camera_color_optical"], dtype=float)
    radius = (
        float(args.object_radius_m)
        if args.object_radius_m is not None
        else float(config["grasp_compensation"]["object_surface_to_grasp_center_m"])
    )
    groups = [_load_group(path, radius) for path in args.logs]
    rotation, means, spread, change = fit(
        groups,
        matrix[:3, :3],
        matrix[:3, 3],
        prior_weight=args.prior_weight,
        max_change_deg=args.max_change_deg,
    )
    result = {
        "candidate_T_wrist_camera": [
            [float(rotation[row, col]) for col in range(3)] + [float(matrix[row, 3])]
            for row in range(3)
        ] + [[0.0, 0.0, 0.0, 1.0]],
        "group_mean_target_base_xyz_m": means.tolist(),
        "max_pairwise_spread_m": spread,
        "rotation_change_from_seed_deg": change,
        "object_radius_m": radius,
        "sample_counts": [len(group) for group in groups],
        "warning": "candidate only; run a fresh independent multi-pose validation before enabling motion",
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
