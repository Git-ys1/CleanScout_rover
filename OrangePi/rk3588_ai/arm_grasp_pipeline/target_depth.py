# coding: utf-8
"""Depth extraction from YOLO boxes. Uses depth ROI median, never area-estimated distance."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np


@dataclass(frozen=True)
class BBox:
    x1: int
    y1: int
    x2: int
    y2: int
    score: float = 1.0
    cls: str = "target"

    @property
    def center(self) -> Tuple[float, float]:
        return ((self.x1 + self.x2) / 2.0, (self.y1 + self.y2) / 2.0)


def median_depth_in_bbox(
    depth_m: np.ndarray,
    bbox: BBox,
    inner_ratio: float = 0.35,
    min_depth_m: Optional[float] = None,
    max_depth_m: Optional[float] = None,
) -> Optional[float]:
    """Return robust target depth from the center ROI of a detection bbox."""
    h, w = depth_m.shape[:2]
    cx, cy = bbox.center
    bw = max(4.0, (bbox.x2 - bbox.x1) * inner_ratio)
    bh = max(4.0, (bbox.y2 - bbox.y1) * inner_ratio)
    x1 = int(max(0, round(cx - bw / 2)))
    x2 = int(min(w, round(cx + bw / 2)))
    y1 = int(max(0, round(cy - bh / 2)))
    y2 = int(min(h, round(cy + bh / 2)))
    roi = np.asarray(depth_m[y1:y2, x1:x2], dtype=float)
    valid = roi[(roi > 0.0) & np.isfinite(roi)]
    if min_depth_m is not None:
        valid = valid[valid >= min_depth_m]
    if max_depth_m is not None:
        valid = valid[valid <= max_depth_m]
    if valid.size < 6:
        return None
    lo, hi = np.percentile(valid, [15, 85])
    trimmed = valid[(valid >= lo) & (valid <= hi)]
    if trimmed.size < 3:
        trimmed = valid
    return float(np.median(trimmed))


def stable_bbox(history: List[BBox], max_center_jitter_px: float = 10.0, min_frames: int = 5) -> Optional[BBox]:
    if len(history) < min_frames:
        return None
    last = history[-min_frames:]
    centers = np.array([b.center for b in last], dtype=float)
    if float(np.max(np.linalg.norm(centers - np.mean(centers, axis=0), axis=1))) > max_center_jitter_px:
        return None
    # Use highest score among the stable window, but keep recent class/name.
    return max(last, key=lambda b: b.score)
