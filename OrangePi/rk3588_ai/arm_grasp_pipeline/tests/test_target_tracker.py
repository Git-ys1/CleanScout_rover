from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.target_depth import BBox  # noqa: E402
from arm_grasp_pipeline.target_tracker import (  # noqa: E402
    TargetTracker,
    TrackResult,
    TrackingStatus,
)


def bottle(x1, y1, x2, y2, score=0.9):
    return BBox(x1, y1, x2, y2, score, "bottle")


class TargetTrackerTests(unittest.TestCase):
    def test_same_track_must_stabilise_and_uses_current_bbox(self):
        tracker = TargetTracker(stable_frames=3, ambiguity_margin=0.02)
        first = tracker.update_result(
            [bottle(300, 210, 340, 270, 0.99)], 1.0, image_shape=(480, 640)
        )
        second_box = bottle(302, 211, 342, 271, 0.60)
        second = tracker.update_result([second_box], 2.0, image_shape=(480, 640))
        current_box = bottle(304, 212, 344, 272, 0.55)
        third = tracker.update_result([current_box], 3.0, image_shape=(480, 640))

        self.assertIsInstance(third, TrackResult)
        self.assertEqual(first.track_id, second.track_id)
        self.assertEqual(second.track_id, third.track_id)
        self.assertFalse(first.stable)
        self.assertFalse(second.stable)
        self.assertTrue(third.stable)
        self.assertTrue(third.motion_allowed)
        self.assertEqual(third.bbox, current_box)
        self.assertEqual(third.target.observation_timestamp, 3.0)

    def test_iou_keeps_lock_instead_of_switching_to_high_confidence_bottle(self):
        tracker = TargetTracker(stable_frames=1, ambiguity_margin=0.02)
        acquired = tracker.update_result(
            [bottle(40, 40, 80, 100)], 1.0, image_shape=(480, 640)
        )
        same = bottle(43, 42, 83, 102, 0.55)
        other = bottle(280, 180, 340, 280, 0.99)
        result = tracker.update_result([other, same], 2.0, image_shape=(480, 640))

        self.assertEqual(result.status, TrackingStatus.TRACKING)
        self.assertEqual(result.track_id, acquired.track_id)
        self.assertEqual(result.bbox, same)
        self.assertFalse(result.switched)

    def test_ambiguous_candidates_return_no_motion_target(self):
        tracker = TargetTracker(stable_frames=1, ambiguity_margin=0.08)
        tracker.update_result(
            [bottle(100, 100, 140, 160)], 1.0, image_shape=(480, 640)
        )
        result = tracker.update_result(
            [
                bottle(99, 100, 139, 160, 0.9),
                bottle(101, 100, 141, 160, 0.9),
            ],
            2.0,
            image_shape=(480, 640),
        )

        self.assertEqual(result.status, TrackingStatus.AMBIGUOUS)
        self.assertIsNone(result.target)
        self.assertTrue(result.must_stop)
        self.assertIn("ambigu", result.association_reason)

    def test_loss_does_not_jump_and_requires_reset_after_expiry(self):
        tracker = TargetTracker(
            stable_frames=1,
            max_lost_frames=1,
            max_center_distance_px=30.0,
            ambiguity_margin=0.02,
        )
        acquired = tracker.update_result(
            [bottle(10, 10, 40, 50)], 1.0, image_shape=(480, 640)
        )
        unrelated = bottle(250, 200, 300, 280)
        lost = tracker.update_result([unrelated], 2.0, image_shape=(480, 640))
        expired = tracker.update_result([unrelated], 3.0, image_shape=(480, 640))
        switched = tracker.update_result([unrelated], 4.0, image_shape=(480, 640))

        self.assertEqual(lost.status, TrackingStatus.LOST)
        self.assertEqual(lost.locked_track_id, acquired.track_id)
        self.assertEqual(expired.status, TrackingStatus.EXPIRED)
        self.assertEqual(switched.status, TrackingStatus.SWITCHED)
        self.assertTrue(switched.switched)
        self.assertIsNone(switched.target)
        tracker.reset()
        new_target = tracker.update_result(
            [unrelated], 5.0, image_shape=(480, 640)
        )
        self.assertNotEqual(new_target.track_id, acquired.track_id)

    def test_depth_gate_rejects_visual_match_with_large_jump(self):
        tracker = TargetTracker(
            stable_frames=1,
            max_depth_difference_m=0.05,
            ambiguity_margin=0.02,
        )
        tracker.update_result(
            [bottle(100, 100, 140, 160)],
            1.0,
            image_shape=(480, 640),
            depths_m=[0.30],
        )
        result = tracker.update_result(
            [bottle(101, 101, 141, 161)],
            2.0,
            image_shape=(480, 640),
            depths_m=[0.46],
        )
        self.assertEqual(result.status, TrackingStatus.LOST)
        self.assertTrue(result.must_stop)

    def test_center_proximity_alone_cannot_reassociate_nonoverlapping_bottle(self):
        tracker = TargetTracker(
            stable_frames=1,
            max_center_distance_px=90.0,
            ambiguity_margin=0.02,
        )
        tracker.update_result(
            [bottle(100, 100, 120, 140)], 1.0, image_shape=(480, 640)
        )
        nearby_but_separate = bottle(150, 100, 170, 140)
        result = tracker.update_result(
            [nearby_but_separate], 2.0, image_shape=(480, 640)
        )
        self.assertEqual(result.status, TrackingStatus.LOST)
        self.assertIsNone(result.target)

    def test_duplicate_or_old_timestamp_is_rejected_without_mutating_track(self):
        tracker = TargetTracker(stable_frames=1)
        acquired = tracker.update_result(
            [bottle(100, 100, 140, 160)], 10.0, image_shape=(480, 640)
        )
        stale = tracker.update_result(
            [bottle(101, 101, 141, 161)], 10.0, image_shape=(480, 640)
        )
        self.assertEqual(stale.status, TrackingStatus.STALE)
        self.assertTrue(stale.must_stop)
        self.assertEqual(tracker.locked_track_id, acquired.track_id)
        self.assertEqual(tracker.last_observed_target.bbox, acquired.bbox)


if __name__ == "__main__":
    unittest.main()
