#!/usr/bin/env python3
"""Hardware-free checks for bounded D435 visual centering."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.target_depth import BBox
from arm_grasp_pipeline.visual_centering import CenteringConfig, PWMVisualCentering


def main() -> int:
    centerer = PWMVisualCentering(CenteringConfig())
    current = [1500, 1907, 1900, 900, 1500, 1500]
    right_below = centerer.command(BBox(430, 330, 530, 430), (480, 640, 3), current)
    assert right_below[0] < current[0]
    assert right_below[3] < current[3]
    assert abs(right_below[0] - current[0]) <= 12
    assert abs(right_below[3] - current[3]) <= 12
    assert centerer.command(BBox(300, 220, 340, 260), (480, 640, 3), current) == {}

    near_limit = [1000, 1907, 1900, 500, 1500, 1500]
    assert centerer.command(BBox(500, 400, 600, 470), (480, 640, 3), near_limit) == {}
    print("VISUAL_CENTERING_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
