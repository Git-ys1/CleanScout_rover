#!/usr/bin/env python3
"""D435 smoke test: aligned depth-to-color and center depth/intrinsics print."""
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.realsense_source import D435Source


def main() -> int:
    try:
        src = D435Source()
    except ModuleNotFoundError as exc:
        if exc.name == "pyrealsense2":
            print("ERROR: pyrealsense2 is not available. Run tools/realsense_env_check.py first.", file=sys.stderr)
            return 2
        raise
    src.start()
    try:
        for i in range(60):
            frame = src.read()
            h, w = frame.depth_m.shape
            z = float(frame.depth_m[h // 2, w // 2])
            if i % 10 == 0:
                color_shape = None if frame.color_bgr is None else frame.color_bgr.shape
                print(f"frame={i} color={color_shape} depth={frame.depth_m.shape} center_z_m={z:.3f} intr={frame.intrinsics_for_detection}")
            time.sleep(0.02)
    finally:
        src.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
