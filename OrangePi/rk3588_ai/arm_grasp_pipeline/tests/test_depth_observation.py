from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.geometry import CameraIntrinsics  # noqa: E402
from arm_grasp_pipeline.realsense_source import (  # noqa: E402
    FrameFreshnessError,
    RealSenseFrame,
    RealSenseSource,
)
from arm_grasp_pipeline.target_depth import (  # noqa: E402
    BBox,
    DepthObservationError,
    observe_depth_in_bbox,
    observe_depth_from_frame,
    stable_bbox,
)


class DepthObservationTests(unittest.TestCase):
    def test_median_observation_reports_quality_statistics(self):
        depth = np.full((40, 40), 0.420, dtype=float)
        depth[8, 8] = 0.0
        depth[10, 10] = np.nan
        depth[12, 12] = 1.8
        observation = observe_depth_in_bbox(
            depth,
            BBox(0, 0, 40, 40),
            inner_ratio=1.0,
            min_valid_count=20,
            min_valid_ratio=0.9,
            max_mad_m=0.01,
            max_iqr_m=0.02,
        )
        self.assertTrue(observation.ok)
        self.assertAlmostEqual(observation.require_quality(), 0.420, places=6)
        self.assertGreater(observation.valid_ratio, 0.99)
        self.assertEqual(observation.pixel_xy, (20.0, 20.0))
        self.assertIn("mad_m", observation.as_dict())
        self.assertEqual(observation.as_dict()["pixel_xy"], [20.0, 20.0])

    def test_invalid_ratio_fails_explicitly(self):
        depth = np.zeros((20, 20), dtype=float)
        depth[8:12, 8:12] = 0.3
        observation = observe_depth_in_bbox(
            depth,
            BBox(0, 0, 20, 20),
            inner_ratio=1.0,
            min_valid_count=5,
            min_valid_ratio=0.20,
            max_mad_m=None,
            max_iqr_m=None,
        )
        self.assertFalse(observation.ok)
        self.assertIsNone(observation.depth_m)
        self.assertIn("ratio", observation.reason)
        with self.assertRaises(DepthObservationError):
            observation.require_quality()

    def test_dispersion_gate_rejects_unstable_depth(self):
        depth = np.empty((20, 20), dtype=float)
        depth[:10, :] = 0.30
        depth[10:, :] = 0.42
        observation = observe_depth_in_bbox(
            depth,
            BBox(0, 0, 20, 20),
            inner_ratio=1.0,
            min_valid_count=20,
            min_valid_ratio=0.9,
            max_mad_m=0.02,
            max_iqr_m=0.04,
        )
        self.assertFalse(observation.ok)
        self.assertTrue("MAD" in observation.reason or "IQR" in observation.reason)

    def test_front_cluster_selects_nearest_stable_surface(self):
        depth = np.full((40, 40), 0.62, dtype=float)
        depth[5:15, 5:15] = 0.30
        observation = observe_depth_in_bbox(
            depth,
            BBox(0, 0, 40, 40),
            inner_ratio=1.0,
            mode="front_cluster",
            front_cluster_bin_m=0.012,
            min_valid_count=12,
            min_valid_ratio=0.9,
            max_mad_m=0.01,
            max_iqr_m=0.02,
        )
        self.assertTrue(observation.ok)
        self.assertAlmostEqual(observation.depth_m, 0.30, places=6)
        self.assertAlmostEqual(observation.median_m, 0.62, places=6)
        self.assertEqual(observation.selected_count, 100)

    def test_percentile_mode_and_depth_jump_gate(self):
        depth = np.linspace(0.20, 0.40, 400, dtype=float).reshape(20, 20)
        first = observe_depth_in_bbox(
            depth,
            BBox(0, 0, 20, 20),
            inner_ratio=1.0,
            mode="percentile",
            percentile=25.0,
            min_valid_count=20,
            min_valid_ratio=0.9,
            max_mad_m=None,
            max_iqr_m=None,
        )
        self.assertTrue(first.ok)
        self.assertAlmostEqual(first.depth_m, np.percentile(depth, 25.0), places=8)
        jumped = observe_depth_in_bbox(
            np.full((20, 20), 0.50),
            BBox(0, 0, 20, 20),
            inner_ratio=1.0,
            previous_depth_m=first.depth_m,
            max_depth_jump_m=0.05,
            min_valid_count=20,
            min_valid_ratio=0.9,
        )
        self.assertFalse(jumped.ok)
        self.assertIsNone(jumped.depth_m)
        self.assertGreater(jumped.depth_jump_m, 0.05)
        self.assertIn("jump", jumped.reason)

    def test_stable_bbox_returns_current_frame_not_historical_best_score(self):
        history = [
            BBox(10, 10, 30, 30, 0.99, "bottle"),
            BBox(11, 10, 31, 30, 0.80, "bottle"),
            BBox(12, 11, 32, 31, 0.55, "bottle"),
        ]
        self.assertEqual(stable_bbox(history, 5.0, 3), history[-1])


class RealSenseFrameTests(unittest.TestCase):
    def setUp(self):
        self.intr = CameraIntrinsics(fx=600.0, fy=600.0, cx=320.0, cy=240.0)

    def _frame(self, timestamp, *, aligned=True):
        return RealSenseFrame(
            depth_m=np.full((4, 6), 0.4, dtype=np.float32),
            depth_intrinsics=self.intr,
            color_bgr=np.zeros((4, 6, 3), dtype=np.uint8),
            color_intrinsics=self.intr,
            monotonic_timestamp=timestamp,
            device_timestamp_ms=1234.5,
            arrival_monotonic_timestamp=timestamp + 0.01,
            depth_aligned_to_color=aligned,
        )

    def test_aligned_rgbd_and_both_timestamps_are_exposed(self):
        frame = self._frame(10.0)
        self.assertIs(frame.require_aligned_rgbd(), frame)
        self.assertEqual(frame.monotonic_timestamp, 10.0)
        self.assertEqual(frame.device_timestamp, 1234.5)
        self.assertEqual(frame.intrinsics_for_detection, self.intr)

    def test_unaligned_depth_fails_before_bbox_sampling(self):
        with self.assertRaises(FrameFreshnessError):
            self._frame(10.0, aligned=False).require_aligned_rgbd()

    def test_frame_observer_enforces_alignment_and_carries_timestamp(self):
        bbox = BBox(0, 0, 6, 4)
        observation = observe_depth_from_frame(
            self._frame(10.0),
            bbox,
            {
                "mode": "median",
                "roi_inner_ratio": 1.0,
                "min_valid_count": 4,
                "min_valid_ratio": 0.5,
                "max_mad_m": 0.01,
                "max_iqr_m": 0.02,
                "min_depth_m": 0.05,
                "max_depth_m": 2.0,
            },
        )
        self.assertTrue(observation.ok)
        self.assertEqual(observation.observation_timestamp, 10.0)
        with self.assertRaises(FrameFreshnessError):
            observe_depth_from_frame(self._frame(11.0, aligned=False), bbox)

    def test_freshness_is_strictly_later_than_motion_end(self):
        frame = self._frame(10.0)
        self.assertFalse(frame.is_fresh_after(10.0, max_age_s=1.0, now_monotonic_s=10.1))
        self.assertTrue(frame.is_fresh_after(9.9, max_age_s=1.0, now_monotonic_s=10.1))
        with self.assertRaises(FrameFreshnessError):
            frame.require_fresh_after(10.0)

    def test_source_discards_stale_buffered_frames(self):
        class FakeSource:
            align_depth_to_color = True

            def __init__(self, frames):
                self.frames = iter(frames)

            def read(self):
                return next(self.frames)

        stale = self._frame(4.9)
        fresh = self._frame(5.1)
        source = FakeSource([stale, fresh])
        result = RealSenseSource.read_fresh_after(
            source, 5.0, max_age_s=1.0, max_discarded_frames=2
        )
        self.assertIs(result, fresh)


if __name__ == "__main__":
    unittest.main()
