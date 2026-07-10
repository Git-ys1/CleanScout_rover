#!/usr/bin/env python3
"""D430 depth-only smoke test.

Use this today before D435 arrives.  It validates RealSense depth streaming,
metre conversion, intrinsics, ROI median, and pixel/depth projection.  It does
not attempt YOLO detection because D430 has no RGB stream.
"""
from pathlib import Path
import argparse
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.geometry import depth_pixel_to_camera
from arm_grasp_pipeline.realsense_source import D430DepthSource
from arm_grasp_pipeline.target_depth import BBox, median_depth_in_bbox


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--width", type=int, default=640)
    ap.add_argument("--height", type=int, default=480)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--frames", type=int, default=80)
    ap.add_argument("--roi", default="center", help="center or x1,y1,x2,y2")
    ap.add_argument("--min_depth_m", type=float, default=None,
                    help="optional lower bound in metres; omitted means no artificial minimum")
    ap.add_argument("--max_depth_m", type=float, default=None,
                    help="optional upper bound in metres; omitted means no maximum")
    args = ap.parse_args()

    try:
        src = D430DepthSource(args.width, args.height, args.fps)
    except ModuleNotFoundError as exc:
        if exc.name == "pyrealsense2":
            print("ERROR: pyrealsense2 is not available. Run tools/realsense_env_check.py first.", file=sys.stderr)
            return 2
        raise
    src.start()
    try:
        valid_count = 0
        last_valid = None
        valid_ratios = []
        for i in range(args.frames):
            frame = src.read()
            h, w = frame.depth_m.shape[:2]
            valid_mask = np.isfinite(frame.depth_m) & (frame.depth_m > 0.0)
            if args.min_depth_m is not None:
                valid_mask &= frame.depth_m >= args.min_depth_m
            if args.max_depth_m is not None:
                valid_mask &= frame.depth_m <= args.max_depth_m
            valid_ratio = float(np.count_nonzero(valid_mask) / valid_mask.size)
            valid_ratios.append(valid_ratio)
            if args.roi == "center":
                box = BBox(w // 2 - 24, h // 2 - 24, w // 2 + 24, h // 2 + 24, 1.0, "depth_probe")
            else:
                vals = [int(v) for v in args.roi.split(",")]
                if len(vals) != 4:
                    raise ValueError("--roi must be center or x1,y1,x2,y2")
                box = BBox(*vals, score=1.0, cls="depth_probe")
            z = median_depth_in_bbox(
                frame.depth_m,
                box,
                inner_ratio=1.0,
                min_depth_m=args.min_depth_m,
                max_depth_m=args.max_depth_m,
            )
            if z is not None:
                valid_count += 1
                last_valid = z
            if i % 10 == 0:
                p = None if z is None else depth_pixel_to_camera(box.center, z, frame.depth_intrinsics)
                print(f"frame={i} depth={frame.depth_m.shape} valid_ratio={valid_ratio:.4f} "
                      f"roi_z_m={z} point_cam_m={p} intr={frame.depth_intrinsics}")
            time.sleep(0.02)
        print(f"summary frames={args.frames} valid_roi_depth_frames={valid_count} "
              f"mean_valid_ratio={float(np.mean(valid_ratios)):.4f} "
              f"last_valid_z_m={last_valid} min_depth_m={args.min_depth_m} "
              f"max_depth_m={args.max_depth_m}")
    finally:
        src.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
