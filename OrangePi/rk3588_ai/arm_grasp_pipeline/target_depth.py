# coding: utf-8
"""Robust depth observations from RGB-aligned detection ROIs.

The dynamic grasp path consumes :class:`DepthObservation` and must check
``quality_ok`` before using ``depth_m``.  ``median_depth_in_bbox`` and
``stable_bbox`` remain as compatibility helpers for the fixed-view tools.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

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

    @property
    def width(self) -> float:
        return max(0.0, float(self.x2) - float(self.x1))

    @property
    def height(self) -> float:
        return max(0.0, float(self.y2) - float(self.y1))

    @property
    def area(self) -> float:
        return self.width * self.height


class DepthObservationError(RuntimeError):
    """Raised when code attempts to consume a failed depth observation."""


@dataclass(frozen=True)
class DepthObservation:
    """Depth measurement and quality evidence for one current-frame bbox.

    ``median_m`` and ``near_percentile_m`` describe all valid ROI samples.
    ``mad_m`` and ``iqr_m`` describe the population selected by ``mode`` (the
    nearest stable cluster for ``front_cluster``).  ``depth_m`` is deliberately
    ``None`` whenever a gate fails so failed observations cannot accidentally
    drive an approach step.
    """

    depth_m: Optional[float]
    valid_count: int
    valid_ratio: float
    median_m: Optional[float]
    mad_m: Optional[float]
    iqr_m: Optional[float]
    near_percentile_m: Optional[float]
    roi: Tuple[int, int, int, int]
    quality_ok: bool
    mode: str
    pixel_xy: Tuple[float, float]
    reason: str = ""
    selected_count: int = 0
    observation_timestamp: Optional[float] = None
    previous_depth_m: Optional[float] = None
    depth_jump_m: Optional[float] = None

    @property
    def ok(self) -> bool:
        """Short fail-closed alias consumed by the closed-loop state machine."""
        return bool(self.quality_ok and self.depth_m is not None)

    def require_quality(self) -> float:
        """Return the selected depth or raise with the exact failed gate."""
        if not self.quality_ok or self.depth_m is None:
            raise DepthObservationError(self.reason or "depth observation quality failed")
        return float(self.depth_m)

    def as_dict(self) -> Dict[str, Any]:
        value = asdict(self)
        value["roi"] = list(self.roi)
        value["pixel_xy"] = list(self.pixel_xy)
        return value


_SUPPORTED_MODES = frozenset(("median", "front_cluster", "percentile"))


def _roi_bounds(
    shape: Sequence[int],
    bbox: BBox,
    inner_ratio: float,
    pixel_xy: Optional[Sequence[float]] = None,
) -> Tuple[int, int, int, int]:
    if len(shape) < 2:
        raise ValueError("depth_m must be a 2-D image")
    ratio = float(inner_ratio)
    if not math.isfinite(ratio) or ratio <= 0.0 or ratio > 1.0:
        raise ValueError("inner_ratio must be in (0, 1]")
    h, w = int(shape[0]), int(shape[1])
    if pixel_xy is None:
        cx, cy = bbox.center
    else:
        if len(pixel_xy) != 2:
            raise ValueError("pixel_xy must contain u and v")
        cx, cy = float(pixel_xy[0]), float(pixel_xy[1])
        if not math.isfinite(cx) or not math.isfinite(cy):
            raise ValueError("pixel_xy must be finite")
    bw = max(4.0, bbox.width * ratio)
    bh = max(4.0, bbox.height * ratio)
    x1 = int(max(0, min(w, round(cx - bw / 2.0))))
    x2 = int(max(0, min(w, round(cx + bw / 2.0))))
    y1 = int(max(0, min(h, round(cy - bh / 2.0))))
    y2 = int(max(0, min(h, round(cy + bh / 2.0))))
    return x1, y1, x2, y2


def _dispersion(values: np.ndarray) -> Tuple[Optional[float], Optional[float]]:
    if values.size == 0:
        return None, None
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    q25, q75 = np.percentile(values, [25.0, 75.0])
    return mad, float(q75 - q25)


def _nearest_stable_cluster(
    values: np.ndarray,
    window_m: float,
    min_valid_count: int,
) -> np.ndarray:
    """Return the nearest locally dense depth population, or an empty array.

    A sliding metric-depth window avoids histogram-bin-boundary instability.
    Five percent of the ROI (and at least half the configured minimum sample
    count) must support the cluster, so a few invalid near speckles cannot win.
    """
    width = float(window_m)
    if not math.isfinite(width) or width <= 0.0:
        raise ValueError("front_cluster_bin_m must be positive")
    ordered = np.sort(np.asarray(values, dtype=float))
    if ordered.size == 0:
        return ordered
    support = max(3, int(math.ceil(ordered.size * 0.05)), int(math.ceil(min_valid_count / 2.0)))
    for start, near in enumerate(ordered):
        stop = int(np.searchsorted(ordered, near + width, side="right"))
        if stop - start >= support:
            # Include the whole dense metric window, never the farther cluster.
            return ordered[start:stop]
    return np.asarray([], dtype=float)


def observe_depth_in_bbox(
    depth_m: np.ndarray,
    bbox: BBox,
    *,
    inner_ratio: float = 0.35,
    mode: str = "median",
    percentile: float = 25.0,
    front_cluster_bin_m: float = 0.012,
    min_valid_count: int = 12,
    min_valid_ratio: float = 0.15,
    max_mad_m: Optional[float] = 0.025,
    max_iqr_m: Optional[float] = 0.05,
    min_depth_m: Optional[float] = 0.05,
    max_depth_m: Optional[float] = 2.0,
    previous_depth_m: Optional[float] = None,
    max_depth_jump_m: Optional[float] = None,
    observation_timestamp: Optional[float] = None,
    pixel_xy: Optional[Sequence[float]] = None,
) -> DepthObservation:
    """Measure one bbox and apply validity, dispersion, and jump gates.

    The input must already be depth aligned to the RGB image containing
    ``bbox``.  No legacy RGB/depth pixel offset is applied here.
    """
    image = np.asarray(depth_m, dtype=float)
    if image.ndim != 2:
        raise ValueError("depth_m must be a 2-D image aligned to the RGB frame")
    selected_mode = str(mode).strip().lower()
    if selected_mode not in _SUPPORTED_MODES:
        raise ValueError("mode must be one of {}".format(sorted(_SUPPORTED_MODES)))
    if int(min_valid_count) < 1:
        raise ValueError("min_valid_count must be at least 1")
    if not 0.0 <= float(min_valid_ratio) <= 1.0:
        raise ValueError("min_valid_ratio must be in [0, 1]")
    percentile_value = float(percentile)
    if not 0.0 <= percentile_value <= 100.0:
        raise ValueError("percentile must be in [0, 100]")
    if observation_timestamp is not None and not math.isfinite(float(observation_timestamp)):
        raise ValueError("observation_timestamp must be finite")
    for name, value in (
        ("max_mad_m", max_mad_m),
        ("max_iqr_m", max_iqr_m),
        ("max_depth_jump_m", max_depth_jump_m),
    ):
        if value is not None and (not math.isfinite(float(value)) or float(value) < 0.0):
            raise ValueError("{} must be finite and non-negative".format(name))
    if min_depth_m is not None and max_depth_m is not None:
        if float(min_depth_m) > float(max_depth_m):
            raise ValueError("min_depth_m cannot exceed max_depth_m")

    selected_pixel = bbox.center if pixel_xy is None else (float(pixel_xy[0]), float(pixel_xy[1]))
    roi_bounds = _roi_bounds(image.shape, bbox, inner_ratio, selected_pixel)
    x1, y1, x2, y2 = roi_bounds
    roi_values = image[y1:y2, x1:x2].reshape(-1)
    total_count = int(roi_values.size)
    # Filter non-finite samples first so NumPy never compares NaN/Inf while
    # evaluating the physical range gates (important on warning-as-error runs).
    valid = roi_values[np.isfinite(roi_values)]
    valid = valid[valid > 0.0]
    if min_depth_m is not None:
        valid = valid[valid >= float(min_depth_m)]
    if max_depth_m is not None:
        valid = valid[valid <= float(max_depth_m)]
    valid_count = int(valid.size)
    valid_ratio = float(valid_count / total_count) if total_count else 0.0

    median_m = float(np.median(valid)) if valid_count else None
    near_m = float(np.percentile(valid, percentile_value)) if valid_count else None
    population = valid
    selected_depth: Optional[float] = median_m
    selection_reason = ""
    if selected_mode == "percentile":
        selected_depth = near_m
    elif selected_mode == "front_cluster":
        population = _nearest_stable_cluster(valid, front_cluster_bin_m, int(min_valid_count))
        if population.size:
            selected_depth = float(np.median(population))
        else:
            selected_depth = None
            selection_reason = "no stable front depth cluster"

    mad_m, iqr_m = _dispersion(population)
    reason = ""
    if total_count == 0:
        reason = "depth ROI is empty"
    elif valid_count < int(min_valid_count):
        reason = "valid depth count {} is below {}".format(valid_count, int(min_valid_count))
    elif valid_ratio < float(min_valid_ratio):
        reason = "valid depth ratio {:.3f} is below {:.3f}".format(valid_ratio, float(min_valid_ratio))
    elif selection_reason:
        reason = selection_reason
    elif selected_depth is None or not math.isfinite(float(selected_depth)):
        reason = "selected depth is invalid"
    elif max_mad_m is not None and (mad_m is None or mad_m > float(max_mad_m)):
        reason = "depth MAD {:.6f} m exceeds {:.6f} m".format(float(mad_m), float(max_mad_m))
    elif max_iqr_m is not None and (iqr_m is None or iqr_m > float(max_iqr_m)):
        reason = "depth IQR {:.6f} m exceeds {:.6f} m".format(float(iqr_m), float(max_iqr_m))

    jump_m = None
    previous = None if previous_depth_m is None else float(previous_depth_m)
    if previous is not None:
        if not math.isfinite(previous) or previous <= 0.0:
            raise ValueError("previous_depth_m must be finite and positive")
        if selected_depth is not None:
            jump_m = abs(float(selected_depth) - previous)
            if (
                not reason
                and max_depth_jump_m is not None
                and jump_m > float(max_depth_jump_m)
            ):
                reason = "depth jump {:.6f} m exceeds {:.6f} m".format(
                    jump_m, float(max_depth_jump_m)
                )

    quality_ok = not reason
    return DepthObservation(
        depth_m=float(selected_depth) if quality_ok and selected_depth is not None else None,
        valid_count=valid_count,
        valid_ratio=valid_ratio,
        median_m=median_m,
        mad_m=mad_m,
        iqr_m=iqr_m,
        near_percentile_m=near_m,
        roi=roi_bounds,
        quality_ok=quality_ok,
        mode=selected_mode,
        pixel_xy=(float(selected_pixel[0]), float(selected_pixel[1])),
        reason=reason,
        selected_count=int(population.size),
        observation_timestamp=None if observation_timestamp is None else float(observation_timestamp),
        previous_depth_m=previous,
        depth_jump_m=jump_m,
    )


# Descriptive aliases retained to keep callers readable across the refactor.
depth_observation_in_bbox = observe_depth_in_bbox
measure_depth_in_bbox = observe_depth_in_bbox


def observe_depth_from_frame(
    frame: Any,
    bbox: BBox,
    config: Optional[Mapping[str, Any]] = None,
    **overrides: Any
) -> DepthObservation:
    """Measure a bbox only after the frame proves RGB/depth alignment.

    ``config`` accepts the repository ``depth_observation`` object directly;
    its ``roi_inner_ratio`` key is mapped to this module's ``inner_ratio``.
    """
    frame.require_aligned_rgbd()
    options: Dict[str, Any] = dict(config or {})
    # Runtime orchestration uses this field to choose ``pixel_xy`` before
    # calling the pure depth estimator; it is not itself an estimator option.
    options.pop("sample_pixel_y_ratio", None)
    if "roi_inner_ratio" in options:
        if "inner_ratio" in options:
            raise ValueError("config cannot contain both roi_inner_ratio and inner_ratio")
        options["inner_ratio"] = options.pop("roi_inner_ratio")
    options.update(overrides)
    options.setdefault("observation_timestamp", float(frame.monotonic_timestamp))
    return observe_depth_in_bbox(frame.depth_m, bbox, **options)


def median_depth_in_bbox(
    depth_m: np.ndarray,
    bbox: BBox,
    inner_ratio: float = 0.35,
    min_depth_m: Optional[float] = None,
    max_depth_m: Optional[float] = None,
) -> Optional[float]:
    """Compatibility wrapper returning only a median or ``None``.

    New closed-loop code must use :func:`observe_depth_in_bbox` so it cannot
    ignore the quality evidence.
    """
    observation = observe_depth_in_bbox(
        depth_m,
        bbox,
        inner_ratio=inner_ratio,
        mode="median",
        min_valid_count=6,
        min_valid_ratio=0.0,
        max_mad_m=None,
        max_iqr_m=None,
        min_depth_m=min_depth_m,
        max_depth_m=max_depth_m,
    )
    return observation.depth_m


def stable_bbox(
    history: List[BBox],
    max_center_jitter_px: float = 10.0,
    min_frames: int = 5,
) -> Optional[BBox]:
    """Return the *current-frame* bbox when the recent centers are stable.

    The previous implementation returned the historical highest-confidence
    box, which could read current depth at stale pixels.  Stability is still
    measured over the window, but depth is now always sampled from ``last``.
    """
    if len(history) < int(min_frames):
        return None
    last = history[-int(min_frames):]
    centers = np.asarray([box.center for box in last], dtype=float)
    center_median = np.median(centers, axis=0)
    jitter = np.linalg.norm(centers - center_median, axis=1)
    if float(np.max(jitter)) > float(max_center_jitter_px):
        return None
    return last[-1]


__all__ = [
    "BBox",
    "DepthObservation",
    "DepthObservationError",
    "depth_observation_in_bbox",
    "measure_depth_in_bbox",
    "median_depth_in_bbox",
    "observe_depth_in_bbox",
    "observe_depth_from_frame",
    "stable_bbox",
]
