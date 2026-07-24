#!/usr/bin/env python3
# coding: utf-8
"""Configure and validate wrist-camera plus open/closed TCP transforms.

Examples (millimetres are explicit)::

  python3 tools/configure_hand_eye_tcp.py --check-only
  python3 tools/configure_hand_eye_tcp.py \
    --camera-reference-tcp closed \
    --camera-origin-in-tcp-mm=-60,32,13 \
    --camera-axis-map=-y,-z,+x \
    --wrist-tcp-open-mm=116,0,0 \
    --wrist-tcp-closed-mm=135,0,0 \
    --mark-hand-eye-calibrated --write

``T_parent_child`` always converts child coordinates into parent coordinates.
In particular, a positive closed TCP X here means "the TCP origin is in front
of the Servo004-stator wrist origin".  It is not the inverse statement
"the wrist is -135 mm in TCP".
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import shutil
import sys
from typing import Iterable, Optional

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.geometry import (  # noqa: E402
    FrameTransforms,
    axis_mapping_to_rotation,
    invert_transform,
    matrix_from_translation_rotation,
    rotation_difference_deg,
    transforms_consistent,
    validate_rigid_transform,
)


DEFAULT_CONFIG = ROOT / "config/arm_grasp_default.json"


def _csv_vector(text: str, scale: float, name: str) -> np.ndarray:
    try:
        values = [float(part.strip()) * scale for part in str(text).split(",")]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("{} must be x,y,z".format(name)) from exc
    vector = np.asarray(values, dtype=float)
    if vector.shape != (3,) or not np.all(np.isfinite(vector)):
        raise argparse.ArgumentTypeError("{} must contain three finite values".format(name))
    if float(np.linalg.norm(vector)) > 1.0:
        raise argparse.ArgumentTypeError(
            "{} exceeds 1 metre; check mm/m units".format(name)
        )
    return vector


def _matrix_rows(matrix: np.ndarray):
    return [[float(value) for value in row] for row in matrix]


def _format_matrix(matrix: np.ndarray) -> str:
    return "\n".join(
        "  [" + ", ".join("{:+.6f}".format(float(value)) for value in row) + "]"
        for row in matrix
    )


def _load(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _backup(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(path.name + ".bak." + stamp)
    shutil.copy2(str(path), str(backup))
    return backup


def parse_args(argv: Optional[Iterable[str]] = None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--replace-existing", action="store_true")
    parser.add_argument("--report", default="")
    parser.add_argument(
        "--camera-reference-tcp", choices=("open", "closed"), default="closed"
    )
    parser.add_argument(
        "--camera-origin-in-tcp-mm",
        default="",
        help="RGB optical origin expressed in the chosen TCP physical axes, millimetres",
    )
    parser.add_argument(
        "--camera-axis-map",
        default="",
        help="camera +X,+Y,+Z expressed in wrist axes, e.g. -y,-z,+x",
    )
    parser.add_argument("--wrist-tcp-open-mm", default="")
    parser.add_argument("--wrist-tcp-closed-mm", default="")
    parser.add_argument(
        "--closed-tcp-vertical-down-from-rgb-mm",
        type=float,
        default=None,
        help="physical evidence only; stored separately and never treated as optical Z",
    )
    parser.add_argument("--mark-hand-eye-calibrated", action="store_true")
    parser.add_argument("--mark-open-calibrated", action="store_true")
    parser.add_argument("--mark-closed-calibrated", action="store_true")
    parser.add_argument("--translation-tolerance-mm", type=float, default=2.0)
    parser.add_argument("--rotation-tolerance-deg", type=float, default=1.0)
    return parser.parse_args(argv)


def _translation_from_matrix(config, name: str) -> np.ndarray:
    matrix = validate_rigid_transform(
        config["tool_tcp"][name], "tool_tcp." + name, max_translation_m=1.0
    )
    return matrix[:3, 3].copy()


def _build_report(config_path: Path, frames: FrameTransforms, config) -> str:
    camera = frames.T_wrist_camera
    open_tcp = frames.T_wrist_tcp_open
    closed_tcp = frames.T_wrist_tcp_closed
    camera_open = invert_transform(open_tcp) @ camera
    camera_closed = invert_transform(closed_tcp) @ camera
    record = config.get("hand_eye", {}).get("measurement_record", {})
    measured_vertical = record.get("closed_tcp_vertical_down_from_rgb_origin_m")
    matrix_vertical = float(camera_closed[2, 3])
    vertical_error = (
        None
        if measured_vertical is None
        else abs(matrix_vertical - float(measured_vertical))
    )
    lines = [
        "# Hand-eye and TCP configuration report",
        "",
        "- Config: `{}`".format(config_path),
        "- Convention: `T_parent_child` converts child into parent.",
        "- Servo004: fixed at PWM `{}`.".format(frames.servo004_fixed_pwm),
        "- hand_eye.calibrated: `{}`".format(frames.hand_eye_calibrated),
        "- tool_tcp.open_calibrated: `{}`".format(frames.open_calibrated),
        "- tool_tcp.closed_calibrated: `{}`".format(frames.closed_calibrated),
        "- active_grasp_tcp: `{}`".format(frames.active_grasp_tcp),
        "",
        "## Positions in wrist coordinates",
        "",
        "- RGB color optical origin: `{}` m".format(camera[:3, 3].tolist()),
        "- open TCP origin: `{}` m".format(open_tcp[:3, 3].tolist()),
        "- closed TCP origin: `{}` m".format(closed_tcp[:3, 3].tolist()),
        "- camera to open TCP distance: `{:.3f}` mm".format(
            float(np.linalg.norm(camera_open[:3, 3])) * 1000.0
        ),
        "- camera to closed TCP distance: `{:.3f}` mm".format(
            float(np.linalg.norm(camera_closed[:3, 3])) * 1000.0
        ),
        "- RGB origin in closed-TCP physical axes: `{}` m".format(
            camera_closed[:3, 3].tolist()
        ),
        "- recorded closed TCP physical vertical-down from RGB: `{}` m; this is not optical Z.".format(
            measured_vertical
        ),
        "- vertical measurement vs matrix error: `{}` mm; consistent within 2 mm: `{}`.".format(
            None if vertical_error is None else vertical_error * 1000.0,
            None if vertical_error is None else vertical_error <= 0.002,
        ),
        "",
        "## Matrices",
        "",
        "### T_wrist_camera_color_optical",
        "```text",
        _format_matrix(camera),
        "```",
        "### T_wrist_tcp_open",
        "```text",
        _format_matrix(open_tcp),
        "```",
        "### T_wrist_tcp_closed",
        "```text",
        _format_matrix(closed_tcp),
        "```",
        "",
        "Direction reminder: `T_wrist_tcp_closed[:3,3]=[+0.135,0,0]` means the closed TCP is 135 mm in front of the wrist; the inverse transform places the wrist at -135 mm in TCP.",
    ]
    return "\n".join(lines) + "\n"


def configure(args) -> int:
    config_path = Path(args.config).expanduser().resolve()
    config = _load(config_path)
    existing = FrameTransforms.from_config(config, require_calibrated=False)

    open_xyz = _translation_from_matrix(config, "T_wrist_tcp_open")
    closed_xyz = _translation_from_matrix(config, "T_wrist_tcp_closed")
    if args.wrist_tcp_open_mm:
        open_xyz = _csv_vector(args.wrist_tcp_open_mm, 0.001, "wrist TCP open")
    if args.wrist_tcp_closed_mm:
        closed_xyz = _csv_vector(args.wrist_tcp_closed_mm, 0.001, "wrist TCP closed")
    T_wrist_tcp_open = matrix_from_translation_rotation(open_xyz)
    T_wrist_tcp_closed = matrix_from_translation_rotation(closed_xyz)

    candidate_camera = existing.T_wrist_camera
    supplied_measurement = bool(args.camera_origin_in_tcp_mm or args.camera_axis_map)
    if supplied_measurement:
        if not args.camera_origin_in_tcp_mm or not args.camera_axis_map:
            raise ValueError(
                "camera measurement requires both --camera-origin-in-tcp-mm and --camera-axis-map"
            )
        camera_in_tcp = _csv_vector(
            args.camera_origin_in_tcp_mm, 0.001, "camera origin in TCP"
        )
        rotation = axis_mapping_to_rotation(args.camera_axis_map)
        reference_tcp = (
            T_wrist_tcp_open
            if args.camera_reference_tcp == "open"
            else T_wrist_tcp_closed
        )
        camera_origin_wrist = (
            reference_tcp[:3, 3]
            + reference_tcp[:3, :3] @ camera_in_tcp
        )
        candidate_camera = matrix_from_translation_rotation(
            camera_origin_wrist, rotation
        )
        consistent = transforms_consistent(
            existing.T_wrist_camera,
            candidate_camera,
            float(args.translation_tolerance_mm) / 1000.0,
            float(args.rotation_tolerance_deg),
        )
        if not consistent and not args.replace_existing:
            translation_mm = float(
                np.linalg.norm(
                    existing.T_wrist_camera[:3, 3] - candidate_camera[:3, 3]
                )
            ) * 1000.0
            rotation_deg = rotation_difference_deg(
                existing.T_wrist_camera, candidate_camera
            )
            raise ValueError(
                "measurement conflicts with existing matrix by {:.3f} mm / {:.3f} deg; inspect with --check-only or pass --replace-existing".format(
                    translation_mm, rotation_deg
                )
            )

    validate_rigid_transform(
        candidate_camera, "T_wrist_camera_color_optical", max_translation_m=1.0
    )
    validate_rigid_transform(
        T_wrist_tcp_open, "T_wrist_tcp_open", max_translation_m=1.0
    )
    validate_rigid_transform(
        T_wrist_tcp_closed, "T_wrist_tcp_closed", max_translation_m=1.0
    )

    config["hand_eye"]["T_wrist_camera_color_optical"] = _matrix_rows(
        candidate_camera
    )
    config["tool_tcp"]["T_wrist_tcp_open"] = _matrix_rows(T_wrist_tcp_open)
    config["tool_tcp"]["T_wrist_tcp_closed"] = _matrix_rows(T_wrist_tcp_closed)
    if supplied_measurement:
        config["hand_eye"]["input_mode"] = "measured_axis_map"
        config["hand_eye"]["measurement_source"] = (
            "configure_hand_eye_tcp.py camera origin + explicit axis mapping"
        )
        config["hand_eye"]["measurement_record"][
            "camera_origin_in_{}_tcp_xyz_m".format(args.camera_reference_tcp)
        ] = [float(value) for value in _csv_vector(
            args.camera_origin_in_tcp_mm, 0.001, "camera origin in TCP"
        )]
        config["hand_eye"]["measurement_record"]["camera_axis_mapping"] = str(
            args.camera_axis_map
        )
    if args.closed_tcp_vertical_down_from_rgb_mm is not None:
        value = float(args.closed_tcp_vertical_down_from_rgb_mm) / 1000.0
        if not np.isfinite(value) or value < 0.0 or value > 0.5:
            raise ValueError("closed TCP vertical difference must be 0..500 mm")
        config["hand_eye"]["measurement_record"][
            "closed_tcp_vertical_down_from_rgb_origin_m"
        ] = value
    if args.mark_hand_eye_calibrated:
        if not supplied_measurement:
            raise ValueError(
                "marking hand-eye calibrated requires a new camera measurement and axis map"
            )
        recorded_vertical = config["hand_eye"]["measurement_record"].get(
            "closed_tcp_vertical_down_from_rgb_origin_m"
        )
        if recorded_vertical is None:
            raise ValueError(
                "marking hand-eye calibrated requires the RGB-to-closed-TCP vertical measurement"
            )
        candidate_in_closed = invert_transform(T_wrist_tcp_closed) @ candidate_camera
        vertical_error_m = abs(
            float(candidate_in_closed[2, 3]) - float(recorded_vertical)
        )
        if vertical_error_m > float(args.translation_tolerance_mm) / 1000.0:
            raise ValueError(
                "camera matrix conflicts with measured RGB-to-closed-TCP vertical by {:.3f} mm"
                .format(vertical_error_m * 1000.0)
            )
        config["hand_eye"]["calibrated"] = True
    if args.mark_open_calibrated:
        config["tool_tcp"]["open_calibrated"] = True
    if args.mark_closed_calibrated:
        config["tool_tcp"]["closed_calibrated"] = True

    checked = FrameTransforms.from_config(config, require_calibrated=False)
    report = _build_report(config_path, checked, config)
    print(report)

    if args.write and args.check_only:
        raise ValueError("--write and --check-only are mutually exclusive")
    if args.write:
        backup = _backup(config_path)
        with config_path.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(config, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        print("CONFIG_BACKUP {}".format(backup))
        print("CONFIG_WRITTEN {}".format(config_path))
    else:
        print("CHECK_ONLY config_not_modified=true")

    if args.report:
        report_path = Path(args.report).expanduser()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8")
        print("REPORT_WRITTEN {}".format(report_path))
    return 0


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    return configure(args)


if __name__ == "__main__":
    raise SystemExit(main())
