#!/usr/bin/env python3
"""Offline regression for C-5.2.2 repeat-grasp verification matching."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.target_depth import BBox
from arm_grasp_pipeline.tools.d435_yolo_grasp import same_target_observation


def main() -> int:
    reference_center = (320.0, 240.0)
    reference_depth = 0.32
    same = BBox(300, 180, 340, 300, score=0.9, cls="bottle")
    moved = BBox(430, 180, 470, 300, score=0.9, cls="bottle")

    assert same_target_observation(reference_center, reference_depth, same, 0.34, 80.0, 0.05)
    assert not same_target_observation(reference_center, reference_depth, moved, 0.34, 80.0, 0.05)
    assert not same_target_observation(reference_center, reference_depth, same, 0.40, 80.0, 0.05)
    assert not same_target_observation(reference_center, reference_depth, None, None, 80.0, 0.05)
    print("REPEAT_GRASP_LOGIC_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
