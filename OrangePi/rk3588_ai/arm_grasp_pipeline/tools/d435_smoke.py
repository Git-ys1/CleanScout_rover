#!/usr/bin/env python3
"""D435 smoke test: aligned RGB-D, robust ROI depth, and evidence images."""
from pathlib import Path
import argparse
import sys
import time

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.geometry import depth_pixel_to_camera
from arm_grasp_pipeline.realsense_source import D435Source
from arm_grasp_pipeline.target_depth import BBox, median_depth_in_bbox


def parse_roi(value: str, width: int, height: int) -> BBox:
    if value == "center":
        return BBox(width // 2 - 24, height // 2 - 24,
                    width // 2 + 24, height // 2 + 24,
                    1.0, "depth_probe")
    values = [int(item) for item in value.split(",")]
    if len(values) != 4:
        raise ValueError("--roi must be center or x1,y1,x2,y2")
    return BBox(*values, score=1.0, cls="depth_probe")


def save_evidence(output_dir: Path, color_bgr: np.ndarray, depth_m: np.ndarray) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    depth_mm = np.clip(depth_m * 1000.0, 0, 65535).astype(np.uint16)
    valid = depth_m[np.isfinite(depth_m) & (depth_m > 0.0)]
    if valid.size:
        lo, hi = np.percentile(valid, [5, 95])
        scale = max(float(hi - lo), 1e-6)
        preview = np.clip((depth_m - lo) / scale, 0.0, 1.0)
        preview = cv2.applyColorMap((preview * 255).astype(np.uint8), cv2.COLORMAP_TURBO)
        preview[depth_m <= 0.0] = 0
    else:
        preview = np.zeros((*depth_m.shape, 3), dtype=np.uint8)
    cv2.imwrite(str(output_dir / "color.png"), color_bgr)
    cv2.imwrite(str(output_dir / "aligned_depth_mm.png"), depth_mm)
    cv2.imwrite(str(output_dir / "aligned_depth_preview.png"), preview)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--frames", type=int, default=60)
    parser.add_argument("--roi", default="center", help="center or x1,y1,x2,y2")
    parser.add_argument("--min_depth_m", type=float, default=None,
                        help="optional lower bound in metres; omitted means no artificial minimum")
    parser.add_argument("--max_depth_m", type=float, default=None,
                        help="optional upper bound in metres; omitted means no maximum")
    parser.add_argument("--save_dir", type=Path, default=None)
    args = parser.parse_args()

    try:
        src = D435Source(args.width, args.height, args.fps)
    except ModuleNotFoundError as exc:
        if exc.name == "pyrealsense2":
            print("ERROR: pyrealsense2 is not available. Run tools/realsense_env_check.py first.", file=sys.stderr)
            return 2
        raise
    src.start()
    try:
        valid_roi_frames = 0
        valid_ratios = []
        last_roi_z = None
        last_frame = None
        for i in range(args.frames):
            frame = src.read()
            h, w = frame.depth_m.shape
            box = parse_roi(args.roi, w, h)
            valid_mask = np.isfinite(frame.depth_m) & (frame.depth_m > 0.0)
            if args.min_depth_m is not None:
                valid_mask &= frame.depth_m >= args.min_depth_m
            if args.max_depth_m is not None:
                valid_mask &= frame.depth_m <= args.max_depth_m
            valid_ratio = float(np.count_nonzero(valid_mask) / valid_mask.size)
            valid_ratios.append(valid_ratio)
            roi_z = median_depth_in_bbox(
                frame.depth_m,
                box,
                inner_ratio=1.0,
                min_depth_m=args.min_depth_m,
                max_depth_m=args.max_depth_m,
            )
            if roi_z is not None:
                valid_roi_frames += 1
                last_roi_z = roi_z
            last_frame = frame
            if i % 10 == 0:
                color_shape = None if frame.color_bgr is None else frame.color_bgr.shape
                point = None if roi_z is None else depth_pixel_to_camera(
                    box.center, roi_z, frame.intrinsics_for_detection)
                print(f"frame={i} color={color_shape} depth={frame.depth_m.shape} "
                      f"valid_ratio={valid_ratio:.4f} roi_z_m={roi_z} "
                      f"point_cam_m={point} intr={frame.intrinsics_for_detection}")
            time.sleep(0.02)
        if args.save_dir is not None and last_frame is not None and last_frame.color_bgr is not None:
            save_evidence(args.save_dir, last_frame.color_bgr, last_frame.depth_m)
        print(f"summary frames={args.frames} valid_roi_depth_frames={valid_roi_frames} "
              f"mean_valid_ratio={float(np.mean(valid_ratios)):.4f} "
              f"last_roi_z_m={last_roi_z} min_depth_m={args.min_depth_m} "
              f"max_depth_m={args.max_depth_m} save_dir={args.save_dir}")
    finally:
        src.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
