# coding: utf-8
"""Lightweight, fail-closed association for the dynamic grasp target.

The tracker intentionally does not guess when two detections fit the locked
target equally well.  During loss/ambiguity it retains the internal lock for a
small reassociation window, but returns no usable target so motion must stop.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import math
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple, Union

from .target_depth import BBox


class TrackingStatus(str, Enum):
    ACQUIRED = "acquired"
    TRACKING = "tracking"
    LOST = "lost"
    AMBIGUOUS = "ambiguous"
    EXPIRED = "expired"
    NO_TARGET = "no_target"
    STALE = "stale_observation"
    SWITCHED = "track_switched"


class TargetTrackingError(RuntimeError):
    """Raised when a failed association is consumed as a motion target."""


@dataclass(frozen=True)
class DetectionCandidate:
    bbox: BBox
    depth_m: Optional[float] = None


@dataclass(frozen=True)
class TrackedTarget:
    track_id: int
    bbox: BBox
    center: Tuple[float, float]
    score: float
    age: int
    lost_count: int
    observation_timestamp: float
    depth_m: Optional[float] = None
    consecutive_hits: int = 1
    stable: bool = False
    association_score: float = 1.0

    def is_fresh(self, now_monotonic_s: float, max_age_s: float) -> bool:
        return (
            math.isfinite(float(now_monotonic_s))
            and float(now_monotonic_s) >= self.observation_timestamp
            and float(now_monotonic_s) - self.observation_timestamp <= float(max_age_s)
        )

    def as_dict(self) -> Dict[str, Any]:
        value = asdict(self)
        value["bbox"] = asdict(self.bbox)
        value["center"] = list(self.center)
        return value


@dataclass(frozen=True)
class TrackingResult:
    status: TrackingStatus
    target: Optional[TrackedTarget]
    locked_track_id: Optional[int]
    reason: str
    candidate_count: int = 0
    ambiguity_score_gap: Optional[float] = None
    switched: bool = False

    @property
    def track_id(self) -> Optional[int]:
        return (
            int(self.target.track_id)
            if self.target is not None
            else self.locked_track_id
        )

    @property
    def bbox(self) -> Optional[BBox]:
        return None if self.target is None else self.target.bbox

    @property
    def stable(self) -> bool:
        return bool(self.target is not None and self.target.stable)

    @property
    def lost(self) -> bool:
        return self.status in (TrackingStatus.LOST, TrackingStatus.EXPIRED)

    @property
    def association_reason(self) -> str:
        return self.reason

    @property
    def ambiguous(self) -> bool:
        return self.status == TrackingStatus.AMBIGUOUS

    def as_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "track_id": self.track_id,
            "locked_track_id": self.locked_track_id,
            "bbox": None if self.bbox is None else asdict(self.bbox),
            "stable": self.stable,
            "switched": bool(self.switched),
            "lost": self.lost,
            "ambiguous": self.ambiguous,
            "association_reason": self.association_reason,
            "candidate_count": int(self.candidate_count),
            "ambiguity_score_gap": self.ambiguity_score_gap,
            "motion_allowed": self.motion_allowed,
            "target": None if self.target is None else self.target.as_dict(),
        }

    @property
    def ok(self) -> bool:
        return self.target is not None and self.status in (
            TrackingStatus.ACQUIRED,
            TrackingStatus.TRACKING,
        )

    @property
    def motion_allowed(self) -> bool:
        return bool(
            self.ok and self.target is not None and self.target.stable and not self.switched
        )

    @property
    def must_stop(self) -> bool:
        return not self.motion_allowed

    def require_target(self, require_stable: bool = True) -> TrackedTarget:
        if not self.ok or self.target is None:
            raise TargetTrackingError(self.reason or self.status.value)
        if require_stable and not self.target.stable:
            raise TargetTrackingError(
                "track {} is not stable ({})".format(
                    self.target.track_id, self.target.consecutive_hits
                )
            )
        return self.target


@dataclass(frozen=True)
class _Association:
    candidate: DetectionCandidate
    similarity: float
    iou: float
    center_distance_px: float
    size_ratio: float
    depth_difference_m: Optional[float]


def bbox_iou(first: BBox, second: BBox) -> float:
    left = max(float(first.x1), float(second.x1))
    top = max(float(first.y1), float(second.y1))
    right = min(float(first.x2), float(second.x2))
    bottom = min(float(first.y2), float(second.y2))
    intersection = max(0.0, right - left) * max(0.0, bottom - top)
    union = first.area + second.area - intersection
    return float(intersection / union) if union > 0.0 else 0.0


class TargetTracker:
    """Associate one locked detection across frames without target hopping."""

    def __init__(
        self,
        target_class: Optional[str] = "bottle",
        initial_strategy: str = "nearest_center",
        min_iou: float = 0.1,
        max_center_distance_px: float = 90.0,
        max_depth_difference_m: float = 0.08,
        max_size_ratio: float = 2.0,
        ambiguity_margin: float = 0.08,
        max_lost_frames: int = 3,
        stable_frames: int = 5,
        max_observation_age_s: Optional[float] = None,
    ) -> None:
        self.target_class = None if target_class is None else str(target_class)
        self.initial_strategy = str(initial_strategy).strip().lower()
        if self.initial_strategy not in ("nearest_center", "highest_score", "highest_confidence"):
            raise ValueError("unsupported initial_strategy: {}".format(initial_strategy))
        self.min_iou = float(min_iou)
        self.max_center_distance_px = float(max_center_distance_px)
        self.max_depth_difference_m = float(max_depth_difference_m)
        self.max_size_ratio = float(max_size_ratio)
        self.ambiguity_margin = float(ambiguity_margin)
        self.max_lost_frames = int(max_lost_frames)
        self.stable_frames = int(stable_frames)
        self.max_observation_age_s = (
            None if max_observation_age_s is None else float(max_observation_age_s)
        )
        if not 0.0 <= self.min_iou <= 1.0:
            raise ValueError("min_iou must be in [0, 1]")
        if self.max_center_distance_px <= 0.0:
            raise ValueError("max_center_distance_px must be positive")
        if self.max_depth_difference_m <= 0.0:
            raise ValueError("max_depth_difference_m must be positive")
        if self.max_size_ratio < 1.0:
            raise ValueError("max_size_ratio must be at least 1")
        if self.ambiguity_margin < 0.0:
            raise ValueError("ambiguity_margin must be non-negative")
        if self.max_lost_frames < 0:
            raise ValueError("max_lost_frames must be non-negative")
        if self.stable_frames < 1:
            raise ValueError("stable_frames must be at least 1")
        if self.max_observation_age_s is not None and self.max_observation_age_s <= 0.0:
            raise ValueError("max_observation_age_s must be positive")

        self._next_track_id = 1
        self._locked: Optional[TrackedTarget] = None
        self._expired_lock_id: Optional[int] = None
        self._last_update_timestamp: Optional[float] = None
        self.last_result = TrackingResult(
            status=TrackingStatus.NO_TARGET,
            target=None,
            locked_track_id=None,
            reason="tracker has no observation",
        )

    @classmethod
    def from_config(
        cls,
        config: Mapping[str, Any],
        *,
        max_observation_age_s: Optional[float] = None,
    ) -> "TargetTracker":
        values = dict(config)
        if max_observation_age_s is not None:
            values["max_observation_age_s"] = max_observation_age_s
        return cls(**values)

    @property
    def locked_track_id(self) -> Optional[int]:
        return None if self._locked is None else int(self._locked.track_id)

    @property
    def last_observed_target(self) -> Optional[TrackedTarget]:
        """Diagnostic state; never use this property to command motion."""
        return self._locked

    def reset(self, *, reset_id_counter: bool = False) -> None:
        self._locked = None
        self._expired_lock_id = None
        self._last_update_timestamp = None
        if reset_id_counter:
            self._next_track_id = 1
        self.last_result = TrackingResult(
            status=TrackingStatus.NO_TARGET,
            target=None,
            locked_track_id=None,
            reason="tracker reset",
        )

    @staticmethod
    def _normalise_candidates(
        detections: Sequence[Union[BBox, DetectionCandidate]],
        depths_m: Optional[Sequence[Optional[float]]],
    ) -> Tuple[DetectionCandidate, ...]:
        if depths_m is not None and len(depths_m) != len(detections):
            raise ValueError("depths_m length must match detections")
        normalised = []
        for index, item in enumerate(detections):
            if isinstance(item, DetectionCandidate):
                if depths_m is not None:
                    raise ValueError("do not pass depths_m with DetectionCandidate inputs")
                candidate = item
            elif isinstance(item, BBox):
                depth = None if depths_m is None else depths_m[index]
                if depth is not None:
                    depth = float(depth)
                    if not math.isfinite(depth) or depth <= 0.0:
                        depth = None
                candidate = DetectionCandidate(item, depth)
            else:
                raise TypeError("detections must contain BBox or DetectionCandidate")
            normalised.append(candidate)
        return tuple(normalised)

    def _class_candidates(self, candidates: Sequence[DetectionCandidate]) -> Tuple[DetectionCandidate, ...]:
        if self._locked is not None:
            required_class = self._locked.bbox.cls
        else:
            required_class = self.target_class
        if required_class is None or required_class == "":
            return tuple(candidates)
        return tuple(candidate for candidate in candidates if candidate.bbox.cls == required_class)

    def _stale_result(self, reason: str) -> TrackingResult:
        result = TrackingResult(
            status=TrackingStatus.STALE,
            target=None,
            locked_track_id=self.locked_track_id,
            reason=reason,
        )
        self.last_result = result
        return result

    def _check_timestamp(self, timestamp: float, now_monotonic_s: Optional[float]) -> Optional[TrackingResult]:
        if not math.isfinite(timestamp):
            raise ValueError("observation_timestamp must be finite")
        if self._last_update_timestamp is not None and timestamp <= self._last_update_timestamp:
            return self._stale_result(
                "observation timestamp {:.6f} is not newer than {:.6f}".format(
                    timestamp, self._last_update_timestamp
                )
            )
        if self.max_observation_age_s is not None and now_monotonic_s is not None:
            now = float(now_monotonic_s)
            if not math.isfinite(now):
                raise ValueError("now_monotonic_s must be finite")
            if timestamp > now:
                return self._stale_result("observation timestamp is in the future")
            age = now - timestamp
            if age > self.max_observation_age_s:
                return self._stale_result(
                    "observation age {:.3f}s exceeds {:.3f}s".format(
                        age, self.max_observation_age_s
                    )
                )
        return None

    def _initial_similarity(
        self,
        candidate: DetectionCandidate,
        image_shape: Optional[Sequence[int]],
    ) -> float:
        confidence = max(0.0, min(1.0, float(candidate.bbox.score)))
        if self.initial_strategy in ("highest_score", "highest_confidence") or image_shape is None:
            return confidence
        if len(image_shape) < 2:
            raise ValueError("image_shape must contain height and width")
        height, width = float(image_shape[0]), float(image_shape[1])
        cx, cy = candidate.bbox.center
        distance = math.hypot(cx - width / 2.0, cy - height / 2.0)
        half_diagonal = max(1.0, math.hypot(width / 2.0, height / 2.0))
        center_score = max(0.0, 1.0 - distance / half_diagonal)
        return 0.75 * center_score + 0.25 * confidence

    def _acquire(
        self,
        candidates: Sequence[DetectionCandidate],
        timestamp: float,
        image_shape: Optional[Sequence[int]],
    ) -> TrackingResult:
        if not candidates:
            result = TrackingResult(
                TrackingStatus.NO_TARGET, None, None, "no matching target detection", 0
            )
            self.last_result = result
            return result
        if self._expired_lock_id is not None:
            result = TrackingResult(
                TrackingStatus.SWITCHED,
                None,
                self._expired_lock_id,
                "new detection would switch expired track {}; reset is required".format(
                    self._expired_lock_id
                ),
                len(candidates),
                None,
                True,
            )
            self.last_result = result
            return result
        ranked = sorted(
            ((self._initial_similarity(candidate, image_shape), candidate) for candidate in candidates),
            key=lambda item: item[0],
            reverse=True,
        )
        gap = None
        if len(ranked) > 1:
            gap = float(ranked[0][0] - ranked[1][0])
            if gap < self.ambiguity_margin:
                result = TrackingResult(
                    TrackingStatus.AMBIGUOUS,
                    None,
                    None,
                    "initial target selection is ambiguous",
                    len(candidates),
                    gap,
                )
                self.last_result = result
                return result
        similarity, candidate = ranked[0]
        track = TrackedTarget(
            track_id=self._next_track_id,
            bbox=candidate.bbox,
            center=candidate.bbox.center,
            score=float(candidate.bbox.score),
            age=1,
            lost_count=0,
            observation_timestamp=timestamp,
            depth_m=candidate.depth_m,
            consecutive_hits=1,
            stable=self.stable_frames <= 1,
            association_score=float(similarity),
        )
        self._next_track_id += 1
        self._locked = track
        result = TrackingResult(
            TrackingStatus.ACQUIRED,
            track,
            track.track_id,
            "target track acquired",
            len(candidates),
            gap,
        )
        self.last_result = result
        return result

    def _association(self, candidate: DetectionCandidate) -> Optional[_Association]:
        assert self._locked is not None
        previous = self._locked
        iou = bbox_iou(previous.bbox, candidate.bbox)
        center_distance = math.hypot(
            candidate.bbox.center[0] - previous.center[0],
            candidate.bbox.center[1] - previous.center[1],
        )
        if iou < self.min_iou and center_distance > self.max_center_distance_px:
            return None
        if iou < self.min_iou and (
            previous.depth_m is None or candidate.depth_m is None
        ):
            # Center proximity alone cannot distinguish two similar bottles.
            # A non-overlapping reassociation therefore requires depth evidence.
            return None
        if previous.lost_count > 0 and iou < self.min_iou:
            # After an actual missed frame, accepting a non-overlapping box can
            # silently jump to a neighbour.  Keep the lock lost/stop instead.
            return None
        if previous.bbox.area <= 0.0 or candidate.bbox.area <= 0.0:
            return None
        size_ratio = max(previous.bbox.area, candidate.bbox.area) / min(
            previous.bbox.area, candidate.bbox.area
        )
        if size_ratio > self.max_size_ratio:
            return None
        depth_difference = None
        if previous.depth_m is not None and candidate.depth_m is not None:
            depth_difference = abs(float(previous.depth_m) - float(candidate.depth_m))
            if depth_difference > self.max_depth_difference_m:
                return None

        center_score = max(0.0, 1.0 - center_distance / self.max_center_distance_px)
        size_score = max(
            0.0,
            1.0 - math.log(max(1.0, size_ratio)) / math.log(self.max_size_ratio)
            if self.max_size_ratio > 1.0
            else float(size_ratio == 1.0),
        )
        depth_score = (
            0.5
            if depth_difference is None
            else max(0.0, 1.0 - depth_difference / self.max_depth_difference_m)
        )
        confidence = max(0.0, min(1.0, float(candidate.bbox.score)))
        similarity = (
            0.50 * iou
            + 0.25 * center_score
            + 0.10 * depth_score
            + 0.10 * size_score
            + 0.05 * confidence
        )
        return _Association(
            candidate=candidate,
            similarity=float(similarity),
            iou=float(iou),
            center_distance_px=float(center_distance),
            size_ratio=float(size_ratio),
            depth_difference_m=depth_difference,
        )

    def _mark_missing(
        self,
        status: TrackingStatus,
        reason: str,
        candidate_count: int,
        gap: Optional[float] = None,
    ) -> TrackingResult:
        assert self._locked is not None
        previous = self._locked
        lost_count = previous.lost_count + 1
        locked_id = previous.track_id
        if lost_count > self.max_lost_frames:
            self._locked = None
            self._expired_lock_id = locked_id
            result = TrackingResult(
                TrackingStatus.EXPIRED,
                None,
                locked_id,
                "{}; track {} expired".format(reason, locked_id),
                candidate_count,
                gap,
            )
        else:
            self._locked = TrackedTarget(
                track_id=previous.track_id,
                bbox=previous.bbox,
                center=previous.center,
                score=previous.score,
                age=previous.age + 1,
                lost_count=lost_count,
                observation_timestamp=previous.observation_timestamp,
                depth_m=previous.depth_m,
                consecutive_hits=0,
                stable=False,
                association_score=previous.association_score,
            )
            result = TrackingResult(
                status,
                None,
                locked_id,
                reason,
                candidate_count,
                gap,
            )
        self.last_result = result
        return result

    def update_result(
        self,
        detections: Sequence[Union[BBox, DetectionCandidate]],
        observation_timestamp: float,
        *,
        image_shape: Optional[Sequence[int]] = None,
        depths_m: Optional[Sequence[Optional[float]]] = None,
        now_monotonic_s: Optional[float] = None,
    ) -> TrackingResult:
        """Process one frame and return explicit association/stop evidence."""
        timestamp = float(observation_timestamp)
        stale = self._check_timestamp(timestamp, now_monotonic_s)
        if stale is not None:
            return stale
        self._last_update_timestamp = timestamp
        candidates = self._class_candidates(self._normalise_candidates(detections, depths_m))
        if self._locked is None:
            return self._acquire(candidates, timestamp, image_shape)
        if not candidates:
            return self._mark_missing(
                TrackingStatus.LOST, "locked target is missing", 0
            )

        associations = [
            association
            for candidate in candidates
            for association in (self._association(candidate),)
            if association is not None
        ]
        associations.sort(key=lambda item: item.similarity, reverse=True)
        if not associations:
            return self._mark_missing(
                TrackingStatus.LOST,
                "no detection passed target association gates",
                len(candidates),
            )
        gap = None
        if len(associations) > 1:
            gap = float(associations[0].similarity - associations[1].similarity)
            if gap < self.ambiguity_margin:
                return self._mark_missing(
                    TrackingStatus.AMBIGUOUS,
                    "multiple detections ambiguously match locked target",
                    len(candidates),
                    gap,
                )

        best = associations[0]
        previous = self._locked
        consecutive_hits = previous.consecutive_hits + 1 if previous.lost_count == 0 else 1
        track = TrackedTarget(
            track_id=previous.track_id,
            bbox=best.candidate.bbox,
            center=best.candidate.bbox.center,
            score=float(best.candidate.bbox.score),
            age=previous.age + 1,
            lost_count=0,
            observation_timestamp=timestamp,
            depth_m=best.candidate.depth_m,
            consecutive_hits=consecutive_hits,
            stable=consecutive_hits >= self.stable_frames,
            association_score=best.similarity,
        )
        self._locked = track
        result = TrackingResult(
            TrackingStatus.TRACKING,
            track,
            track.track_id,
            "locked target associated",
            len(candidates),
            gap,
        )
        self.last_result = result
        return result

    def update(
        self,
        detections: Sequence[Union[BBox, DetectionCandidate]],
        observation_timestamp: float,
        **kwargs: Any
    ) -> Optional[TrackedTarget]:
        """Return the current observed target, or ``None`` on any stop case.

        Inspect :attr:`last_result` for loss, ambiguity, stale-frame, and
        stability details.  ``last_result.motion_allowed`` is the fail-closed
        gate used by the dynamic state machine.
        """
        return self.update_result(detections, observation_timestamp, **kwargs).target

    track = update


__all__ = [
    "BBox",
    "DetectionCandidate",
    "TargetTracker",
    "TargetTrackingError",
    "TrackedTarget",
    "TrackingResult",
    "TrackingStatus",
    "bbox_iou",
]

# Preferred concise public name; keep TrackingResult for callers already using
# the longer spelling during the refactor.
TrackResult = TrackingResult
__all__.append("TrackResult")
