#!/usr/bin/env python3
"""Collect paired camera/base 3D points from an aligned D435 image.

The optional serial preparation moves the arm once to the configured fixed-view
pose, verifies Servo000..004 through PRAD, then closes the serial port before
point collection. No servo command is sent while calibration points are picked.
"""
from __future__ import annotations

import argparse
from collections import deque
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.fixed_view import (
    CALIBRATION_CSV_FIELDS,
    median_depth_around_pixel,
)
from arm_grasp_pipeline.geometry import depth_pixel_to_camera
from arm_grasp_pipeline.realsense_source import D435Source
from arm_grasp_pipeline.serial_servo_adapter import SerialServoArmAdapter


DEFAULT_CONFIG = ROOT / "config/arm_grasp_default.json"
DEFAULT_OUTPUT = Path.home() / "rk3588_ai/calibration/base_camera_points.csv"
WINDOW_NAME = "C-5.2.4 Base-Camera Point Collector"


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--radius_px", type=int, default=4)
    parser.add_argument("--history_frames", type=int, default=12)
    pose_group = parser.add_mutually_exclusive_group()
    pose_group.add_argument(
        "--prepare_reference_pose", action="store_true",
        help="move to the configured fixed-view pose and verify readback",
    )
    pose_group.add_argument(
        "--verify_reference_pose", action="store_true",
        help="read and verify the current pose without moving the arm",
    )
    parser.add_argument("--serial_port", default="")
    parser.add_argument("--baudrate", type=int, default=0)
    parser.add_argument("--pose_duration_ms", type=int, default=5000)
    parser.add_argument("--pose_tolerance_pwm", type=int, default=30)
    parser.add_argument("--serial_timeout_s", type=float, default=0.8)
    parser.add_argument(
        "--pose_check_only", action="store_true",
        help="finish after serial pose preparation/verification; do not open D435",
    )
    parser.add_argument(
        "--session_report", default="",
        help="JSON evidence path; default is next to the output CSV",
    )
    return parser.parse_args()


def load_config(path):
    with Path(path).expanduser().open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_rows(path):
    source = Path(path).expanduser()
    if not source.exists() or source.stat().st_size == 0:
        return []
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != CALIBRATION_CSV_FIELDS:
            raise ValueError(
                "calibration CSV header must be exactly: "
                + ",".join(CALIBRATION_CSV_FIELDS)
            )
        return [dict(row) for row in reader]


def write_rows_atomic(path, rows):
    destination = Path(path).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", newline="", dir=str(destination.parent),
            delete=False, prefix=destination.name + ".", suffix=".tmp") as handle:
        writer = csv.DictWriter(handle, fieldnames=CALIBRATION_CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
        temporary = Path(handle.name)
    temporary.replace(destination)


def write_json_atomic(path, payload):
    destination = Path(path).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=str(destination.parent), delete=False,
            prefix=destination.name + ".", suffix=".tmp") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(destination)


def parse_base_xyz_mm(text):
    normalized = str(text).replace(",", " ").split()
    if len(normalized) != 3:
        raise ValueError("请输入三个数：X前方 Y左侧 Z向上，单位毫米")
    values_mm = np.asarray([float(value) for value in normalized], dtype=float)
    if not np.all(np.isfinite(values_mm)):
        raise ValueError("底座坐标必须是有限数字")
    return values_mm / 1000.0


def pose_mismatches(reference, actual, tolerance, required_ids=range(5)):
    mismatches = {}
    for servo_id in required_ids:
        observed = actual.get(int(servo_id))
        target = int(reference[int(servo_id)])
        if observed is None or abs(int(observed) - target) > int(tolerance):
            mismatches[int(servo_id)] = {
                "target_pwm": target,
                "actual_pwm": observed,
                "delta_pwm": None if observed is None else int(observed) - target,
            }
    return mismatches


def prepare_or_verify_pose(config, args, reference):
    serial_cfg = dict(config.get("serial", {}))
    port = args.serial_port or str(serial_cfg.get("port", "/dev/ttyUSB0"))
    baudrate = args.baudrate or int(serial_cfg.get("baudrate", 115200))
    if int(reference[4]) != 1500:
        raise RuntimeError("fixed-view calibration requires Servo004=1500")
    adapter = SerialServoArmAdapter(
        port=port, baudrate=baudrate, dry_run=False
    )
    evidence = {
        "port": port,
        "baudrate": baudrate,
        "reference_servo_pwms": list(reference),
        "pose_tolerance_pwm": int(args.pose_tolerance_pwm),
        "move_command": None,
        "before_pwms": None,
        "after_pwms": None,
        "verified_servo_ids": [0, 1, 2, 3, 4],
        "servo005_note": "readback recorded when available; it does not move the camera",
    }
    try:
        adapter.connect()
        before = adapter.read_pwms(range(6), timeout_s=args.serial_timeout_s)
        evidence["before_pwms"] = before
        if args.prepare_reference_pose:
            evidence["move_command"] = adapter.send_pwm_command(
                reference, duration_ms=args.pose_duration_ms
            )
            time.sleep(max(0.0, args.pose_duration_ms / 1000.0) + 0.8)
        after = adapter.read_pwms(range(6), timeout_s=args.serial_timeout_s)
        evidence["after_pwms"] = after
        mismatches = pose_mismatches(
            reference, after, args.pose_tolerance_pwm
        )
        evidence["mismatches"] = mismatches
        if mismatches:
            raise RuntimeError(
                "fixed-view pose readback failed: "
                + json.dumps(mismatches, ensure_ascii=False)
            )
        return evidence
    finally:
        adapter.close()


def main() -> int:
    args = parse_args()
    if args.radius_px < 1 or args.history_frames < 3:
        raise ValueError("radius_px must be >=1 and history_frames must be >=3")
    if args.pose_duration_ms < 500 or args.pose_duration_ms > 15000:
        raise ValueError("pose_duration_ms must be in 500..15000")
    if args.pose_tolerance_pwm < 1 or args.pose_tolerance_pwm > 100:
        raise ValueError("pose_tolerance_pwm must be in 1..100")
    if args.pose_check_only and not (
            args.prepare_reference_pose or args.verify_reference_pose):
        raise ValueError(
            "pose_check_only requires prepare_reference_pose or verify_reference_pose"
        )
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("opencv-python with HighGUI is required") from exc

    config = load_config(args.config)
    realsense = dict(config.get("realsense", {}))
    reference = list(config.get("fixed_view_calibration", {}).get(
        "reference_servo_pwms", []
    ))
    if len(reference) != 6:
        raise ValueError("fixed-view reference_servo_pwms must contain six values")
    output = Path(args.output).expanduser()
    report_path = (
        Path(args.session_report).expanduser()
        if args.session_report else output.with_suffix(".session.json")
    )
    rows = read_rows(output)
    click = {"pixel": None}
    depth_history = deque(maxlen=args.history_frames)
    last_pixel = None
    last_camera = None
    serial_evidence = None
    if args.prepare_reference_pose or args.verify_reference_pose:
        try:
            serial_evidence = prepare_or_verify_pose(config, args, reference)
        except RuntimeError as exc:
            print("REFERENCE_POSE_REJECTED {}".format(exc), file=sys.stderr)
            if args.verify_reference_pose:
                print(
                    "当前姿态与参考姿态不同；--verify_reference_pose 只读不动。"
                    "清空机械臂周围后，改用 --prepare_reference_pose 自动恢复。",
                    file=sys.stderr,
                )
            return 2
        print("REFERENCE_POSE_VERIFIED " + json.dumps(
            serial_evidence, ensure_ascii=False
        ))
        if args.pose_check_only:
            print("POSE_CHECK_DONE camera_opened=false")
            return 0

    session = {
        "schema": "cleanscout.base_camera_point_collection.v1",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "config_path": str(Path(args.config).expanduser()),
        "output_csv": str(output),
        "reference_servo_pwms": reference,
        "serial_preparation": serial_evidence,
        "serial_closed_before_camera_collection": serial_evidence is not None,
        "camera": {
            "serial_number": realsense.get("serial_number") or None,
            "width": int(realsense.get("width", 640)),
            "height": int(realsense.get("height", 480)),
            "fps": int(realsense.get("fps", 30)),
            "aligned_depth_to_color": True,
            "intrinsics": None,
        },
        "frames": {
            "camera": "color optical: +X right, +Y down, +Z forward",
            "base": "Servo000 axis/base plane: +X forward, +Y left, +Z up",
            "units_csv": "metres",
            "units_terminal_input": "millimetres",
        },
        "points_collected_this_session": [],
        "total_csv_rows": len(rows),
    }
    write_json_atomic(report_path, session)

    def on_mouse(event, x, y, _flags, _userdata):
        if event == cv2.EVENT_LBUTTONDOWN:
            click["pixel"] = (int(x), int(y))

    source = D435Source(
        int(realsense.get("width", 640)),
        int(realsense.get("height", 480)),
        int(realsense.get("fps", 30)),
        serial_number=realsense.get("serial_number") or None,
    )
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(WINDOW_NAME, on_mouse)
    print("FIXED_VIEW_REFERENCE " + json.dumps({
        "servo_pwms_000_005": reference,
        "output_csv": str(output),
        "existing_rows": len(rows),
        "serial_prepared": serial_evidence is not None,
        "serial_closed_before_collection": serial_evidence is not None,
        "servo_command_sent_during_collection": False,
        "session_report": str(report_path),
    }, ensure_ascii=False))
    print("操作：左键点标记尖端；终端输入底座 X,Y,Z 毫米；u 撤销最后一行；q/ESC 退出。")

    try:
        source.start()
        while True:
            frame = source.read()
            if session["camera"]["intrinsics"] is None:
                intr = frame.intrinsics_for_detection
                session["camera"]["intrinsics"] = {
                    "fx": float(intr.fx), "fy": float(intr.fy),
                    "cx": float(intr.cx), "cy": float(intr.cy),
                }
                write_json_atomic(report_path, session)
            depth_history.append(frame.depth_m.copy())
            visual = frame.color_bgr.copy()
            if last_pixel is not None:
                cv2.drawMarker(
                    visual, last_pixel, (0, 0, 255), cv2.MARKER_CROSS, 24, 2
                )
            lines = [
                "LEFT CLICK: calibration tip",
                "Terminal: enter base X,Y,Z in mm",
                "u: undo last row   q/ESC: quit",
                "rows={}  fixed pose={}".format(len(rows), reference),
            ]
            if last_camera is not None:
                lines.append("camera_m=[{:.4f}, {:.4f}, {:.4f}]".format(*last_camera))
            for index, line in enumerate(lines):
                cv2.putText(
                    visual, line, (12, 28 + index * 26),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 255, 0), 2,
                )
            cv2.imshow(WINDOW_NAME, visual)

            pending = click.pop("pixel", None)
            click["pixel"] = None
            if pending is not None:
                depth = median_depth_around_pixel(
                    np.stack(tuple(depth_history), axis=0), pending,
                    radius_px=args.radius_px,
                )
                if depth is None:
                    print("该像素附近没有足够有效深度，请换一个清晰表面重试。")
                else:
                    camera = depth_pixel_to_camera(
                        pending, depth, frame.intrinsics_for_detection
                    )
                    last_pixel = pending
                    last_camera = camera
                    print("CAMERA_POINT " + json.dumps({
                        "pixel_xy": list(pending),
                        "depth_m": float(depth),
                        "camera_xyz_m": camera.tolist(),
                    }, ensure_ascii=False))
                    raw = input(
                        "输入该尖端的底座坐标 X前方,Y左侧,Z向上（毫米）；"
                        "输入 skip 取消： "
                    ).strip()
                    if raw.lower() not in {"", "skip", "s"}:
                        try:
                            base = parse_base_xyz_mm(raw)
                        except ValueError as exc:
                            print("未保存：{}".format(exc))
                        else:
                            values = np.concatenate([camera, base])
                            row = {
                                name: "{:.9f}".format(float(value))
                                for name, value in zip(CALIBRATION_CSV_FIELDS, values)
                            }
                            rows.append(row)
                            write_rows_atomic(output, rows)
                            point_evidence = {
                                "index": len(rows),
                                "captured_utc": datetime.now(timezone.utc).isoformat(),
                                "pixel_xy": list(pending),
                                "depth_m": float(depth),
                                "camera_xyz_m": camera.tolist(),
                                "base_xyz_m": base.tolist(),
                                "depth_history_frames": int(len(depth_history)),
                                "depth_radius_px": int(args.radius_px),
                            }
                            session["points_collected_this_session"].append(
                                point_evidence
                            )
                            session["total_csv_rows"] = len(rows)
                            write_json_atomic(report_path, session)
                            print("POINT_SAVED " + json.dumps({
                                "row_count": len(rows),
                                "camera_xyz_m": camera.tolist(),
                                "base_xyz_m": base.tolist(),
                                "output_csv": str(output),
                            }, ensure_ascii=False))

            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q")):
                break
            if key == ord("u"):
                if rows:
                    removed = rows.pop()
                    write_rows_atomic(output, rows)
                    if session["points_collected_this_session"]:
                        session["points_collected_this_session"].pop()
                    session["total_csv_rows"] = len(rows)
                    write_json_atomic(report_path, session)
                    print("POINT_UNDONE " + json.dumps({
                        "remaining_rows": len(rows), "removed": removed,
                    }, ensure_ascii=False))
                else:
                    print("没有可撤销的标定点。")
    finally:
        try:
            source.stop()
        except Exception:
            pass
        cv2.destroyAllWindows()

    session["finished_utc"] = datetime.now(timezone.utc).isoformat()
    session["total_csv_rows"] = len(rows)
    write_json_atomic(report_path, session)
    print("COLLECTION_DONE rows={} output={} report={}".format(
        len(rows), output, report_path
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
