#!/usr/bin/env python3
"""Run a repeatable arm-tracking response test.

The sequence is intentionally mechanical:
1. Move to the standard startup pose.
2. Apply a small perturbation while keeping the target in view.
3. Run yolo_arm_track.py with metrics enabled.
4. Let the metrics summary score convergence and shake.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path.home() / "rk3588_ai/rknn_lite_env/bin/python3"
STANDARD_POSE = "0=1500,1=1907,2=1900,3=900,4=1500,5=1500"
DEFAULT_PERTURB_POSE = "0=1540,1=1887,3=930"


def run(cmd, cwd=ROOT):
    print("$ " + " ".join(str(part) for part in cmd))
    subprocess.run([str(part) for part in cmd], cwd=str(cwd), check=True)


def parse_args():
    parser = argparse.ArgumentParser(description="Repeatable C-5.0.9 tracking response test.")
    parser.add_argument("--serial_port", default="/dev/ttyUSB0")
    parser.add_argument("--camera", default="0")
    parser.add_argument("--track_class", default="bottle")
    parser.add_argument("--control_axes", default="yaw,lift,pitch")
    parser.add_argument("--standard_pose", default=STANDARD_POSE)
    parser.add_argument("--perturb_pose", default=DEFAULT_PERTURB_POSE)
    parser.add_argument("--duration_ms", type=int, default=1200)
    parser.add_argument("--settle_s", type=float, default=0.6)
    parser.add_argument("--max_frames", type=int, default=90)
    parser.add_argument("--log_interval", type=int, default=15)
    parser.add_argument("--output_dir", default="~/rk3588_ai/debug_logs/arm_tracking_eval")
    parser.add_argument("--no_show", action="store_true")
    parser.add_argument("--real", action="store_true", help="actually move the arm; otherwise only print the plan")
    return parser.parse_args()


def score_summary(summary):
    if not summary or not summary.get("target_frames"):
        return {"score": 9999.0, "reason": "no target frames"}
    final_x = float(summary.get("final_abs_error_x") or 0.0)
    final_y = float(summary.get("final_abs_error_y") or 0.0)
    mean_x = float(summary.get("mean_abs_error_x") or 0.0)
    mean_y = float(summary.get("mean_abs_error_y") or 0.0)
    shake = 8.0 * (int(summary.get("sign_changes_x") or 0) + int(summary.get("sign_changes_y") or 0))
    miss_penalty = 100.0 * (1.0 - float(summary.get("target_ratio") or 0.0))
    score = (2.0 * final_x) + (2.0 * final_y) + mean_x + mean_y + shake + miss_penalty
    return {
        "score": score,
        "final_abs_error_x": final_x,
        "final_abs_error_y": final_y,
        "mean_abs_error_x": mean_x,
        "mean_abs_error_y": mean_y,
        "shake_penalty": shake,
        "miss_penalty": miss_penalty,
    }


def main():
    args = parse_args()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = Path(args.output_dir).expanduser() / timestamp
    metrics_path = output_dir / "tracking_metrics.jsonl"
    output_dir.mkdir(parents=True, exist_ok=True)

    plan = {
        "standard_pose": args.standard_pose,
        "perturb_pose": args.perturb_pose,
        "duration_ms": args.duration_ms,
        "max_frames": args.max_frames,
        "metrics_path": str(metrics_path),
        "real": bool(args.real),
    }
    print(json.dumps({"plan": plan}, ensure_ascii=False, indent=2))

    if not args.real:
        print("Dry plan only. Add --real to move the arm and run tracking.")
        return 0

    common_set = [
        PYTHON,
        ROOT / "tools/arm_servo_tune.py",
        "--serial_port",
        args.serial_port,
        "--duration_ms",
        str(args.duration_ms),
        "--settle_s",
        str(args.settle_s),
    ]
    run(common_set + ["--set", args.standard_pose])
    time.sleep(max(0.0, args.duration_ms / 1000.0) + max(0.0, args.settle_s))
    run(common_set + ["--set", args.perturb_pose])
    time.sleep(max(0.0, args.duration_ms / 1000.0) + max(0.0, args.settle_s))

    tracking_cmd = [
        PYTHON,
        ROOT / "yolo_arm_track.py",
        "--model_path",
        Path.home() / "rk3588_ai/models/official_yolo11.rknn",
        "--target",
        "rk3588",
        "--camera",
        args.camera,
        "--track_class",
        args.track_class,
        "--control_axes",
        args.control_axes,
        "--serial_port",
        args.serial_port,
        "--dry_run",
        "false",
        "--enable_arm",
        "--prepare_pose",
        "false",
        "--send_initial_axis_pose",
        "false",
        "--print_cmd",
        "--max_frames",
        str(args.max_frames),
        "--log_interval",
        str(args.log_interval),
        "--metrics_path",
        metrics_path,
    ]
    if args.no_show:
        tracking_cmd.append("--no_show")
    run(tracking_cmd)

    summary_path = metrics_path.with_suffix(metrics_path.suffix + ".summary.json")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    score = score_summary(summary)
    score_path = output_dir / "score.json"
    score_path.write_text(json.dumps({"summary": summary, "score": score}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"score_path": str(score_path), "score": score}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
