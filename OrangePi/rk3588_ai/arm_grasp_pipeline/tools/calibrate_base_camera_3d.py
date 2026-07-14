#!/usr/bin/env python3
"""Calibrate fixed-view ``T_base_camera_reference`` from 3D correspondences."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
import tempfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.fixed_view import solve_rigid_transform


CSV_FIELDS = (
    "camera_x", "camera_y", "camera_z",
    "base_x", "base_y", "base_z",
)


def load_correspondences(path):
    camera_points = []
    base_points = []
    with Path(path).expanduser().open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or any(name not in reader.fieldnames for name in CSV_FIELDS):
            raise ValueError("CSV header must contain: " + ",".join(CSV_FIELDS))
        for line_number, row in enumerate(reader, start=2):
            try:
                values = [float(row[name]) for name in CSV_FIELDS]
            except (TypeError, ValueError) as exc:
                raise ValueError("invalid numeric value at CSV line {}".format(line_number)) from exc
            camera_points.append(values[:3])
            base_points.append(values[3:])
    return np.asarray(camera_points, dtype=float), np.asarray(base_points, dtype=float)


def write_json_atomic(path, payload):
    destination = Path(path).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=str(destination.parent), delete=False,
            prefix=destination.name + ".", suffix=".tmp") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temp_path = Path(handle.name)
    temp_path.replace(destination)


def update_config(path, report):
    config_path = Path(path).expanduser()
    with config_path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    section = dict(config.get("fixed_view_calibration", {}))
    section.update({
        "calibrated": bool(report["quality_pass"]),
        "base_to_camera_matrix_4x4": report["base_to_camera_matrix_4x4"],
        "rmse_m": report["rmse_m"],
        "max_error_m": report["max_error_m"],
    })
    config["fixed_view_calibration"] = section
    write_json_atomic(config_path, config)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", help="CSV with camera_x..base_z columns, metres")
    parser.add_argument("--output_json", default="", help="optional calibration report path")
    parser.add_argument("--config", default=str(ROOT / "config/arm_grasp_default.json"))
    parser.add_argument("--write_config", action="store_true",
                        help="write matrix/metrics and quality result into --config")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    camera, base = load_correspondences(args.csv_path)
    result = solve_rigid_transform(camera, base)
    report = result.as_dict()
    report["point_count"] = int(camera.shape[0])
    report["points"] = [
        {
            "index": index,
            "camera_m": camera[index].tolist(),
            "base_m": base[index].tolist(),
            "error_m": float(result.errors_m[index]),
        }
        for index in range(camera.shape[0])
    ]
    if args.output_json:
        write_json_atomic(args.output_json, report)
    if args.write_config:
        update_config(args.config, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["quality_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
