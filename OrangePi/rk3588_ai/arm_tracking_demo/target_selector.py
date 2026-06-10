#!/usr/bin/env python3
"""Select one stable target from YOLO detections."""

from __future__ import annotations

import math
from typing import Dict, Iterable, Optional, Sequence


def normalize_name(value) -> str:
    return str(value).strip().lower().replace(" ", "")


def class_name(class_id, class_names: Optional[Sequence[str]] = None) -> str:
    if isinstance(class_id, str):
        return normalize_name(class_id)
    if class_names is None:
        return str(int(class_id))
    index = int(class_id)
    if index < 0 or index >= len(class_names):
        return str(index)
    return normalize_name(class_names[index])


def select_target(
    boxes,
    classes,
    scores,
    frame_width: int,
    frame_height: int,
    target_class: str = "person",
    conf: float = 0.25,
    strategy: str = "nearest_center",
    class_names: Optional[Sequence[str]] = None,
) -> Optional[Dict[str, object]]:
    if boxes is None or classes is None or scores is None:
        return None

    target_class = normalize_name(target_class)
    frame_cx = frame_width / 2.0
    frame_cy = frame_height / 2.0
    candidates = []

    for box, class_id, score in zip(boxes, classes, scores):
        score = float(score)
        name = class_name(class_id, class_names)
        if score < conf:
            continue
        if target_class != "any" and name != target_class:
            continue

        x1, y1, x2, y2 = [float(value) for value in box]
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        dist = math.hypot(cx - frame_cx, cy - frame_cy)
        candidates.append(
            {
                "box": [x1, y1, x2, y2],
                "class_id": int(class_id) if not isinstance(class_id, str) else class_id,
                "class_name": name,
                "score": score,
                "cx": cx,
                "cy": cy,
                "center_distance": dist,
            }
        )

    if not candidates:
        return None

    if strategy == "highest_conf":
        return max(candidates, key=lambda item: item["score"])
    return min(candidates, key=lambda item: item["center_distance"])
