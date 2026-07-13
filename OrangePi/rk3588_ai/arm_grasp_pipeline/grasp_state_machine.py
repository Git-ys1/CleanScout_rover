# coding: utf-8
"""YOLO bbox + D435 aligned depth -> robust grasp cycle.

Current stage is non-ROS.  A ROS-compatible event sink is still kept at the
boundary so this file can later publish/debug the same state transitions through
ROS2/Noetic without moving IK or geometry out of OrangePi code.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import Enum, auto
import time
from typing import Optional, Tuple

import numpy as np

from .arm_motion import ArmMotion
from .geometry import CameraIntrinsics, HandEye, PixelToBaseDebug, target_pixel_to_base_point_debug
from .ros_compat import ArmTargetMsg, GraspEventMsg, GraspEventSink, NullRosBridge
from .target_depth import BBox, median_depth_in_bbox, stable_bbox


class GraspState(Enum):
    SEARCH = auto()
    CENTERING = auto()
    DEPTH_LOCK = auto()
    OPEN = auto()
    PRE_GRASP = auto()
    APPROACH = auto()
    CLOSE = auto()
    LIFT = auto()
    RETURN_VERIFY = auto()
    VERIFY = auto()
    RETRY = auto()
    FAILED = auto()


@dataclass
class GraspConfig:
    stable_frames: int = 5
    max_center_jitter_px: float = 10.0
    center_tolerance_px: float = 48.0
    depth_stable_frames: int = 4
    max_depth_jitter_m: float = 0.025
    pre_grasp_standoff_m: float = 0.070
    grasp_insert_m: float = 0.0
    lift_raise_m: float = 0.080
    pitch_deg: float = 70.0
    gripper_open_pwm: int = 600
    gripper_close_pwm: int = 2400
    gripper_open_ms: int = 2000
    pre_grasp_ms: int = 1800
    approach_ms: int = 1400
    gripper_close_ms: int = 1800
    lift_ms: int = 1800
    retry_motion_ms: int = 3500
    retry_pose_pwms: Tuple[int, int, int, int, int, int] = (1380, 1909, 1900, 620, 1500, 1500)
    rgb_depth_x_correction_m: float = -0.007
    workspace_min_xyz_m: Tuple[float, float, float] = (0.04, -0.30, 0.015)
    workspace_max_xyz_m: Tuple[float, float, float] = (0.39, 0.30, 0.42)
    motion_settle_s: float = 0.15


class GraspStateMachine:
    def __init__(self, arm: ArmMotion, intr: CameraIntrinsics, cfg: Optional[GraspConfig] = None,
                 hand_eye: HandEye = HandEye(), event_sink: Optional[GraspEventSink] = None) -> None:
        self.arm = arm
        self.intr = intr
        self.cfg = cfg or GraspConfig()
        self.hand_eye = hand_eye
        self.event_sink = event_sink or NullRosBridge()
        self.state = GraspState.SEARCH
        self.history: deque[BBox] = deque(maxlen=max(10, self.cfg.stable_frames + 2))
        self.depth_history: deque[float] = deque(maxlen=max(3, self.cfg.depth_stable_frames))
        self.locked_target_base: Optional[np.ndarray] = None
        self.last_lock_debug: Optional[PixelToBaseDebug] = None

    def _emit(self, state: GraspState, ok: bool, detail: str = "", target_xyz: Optional[np.ndarray] = None,
              gripper: Optional[float] = None) -> None:
        msg_target = None
        if target_xyz is not None:
            msg_target = ArmTargetMsg(
                frame_id="arm_base",
                x_m=float(target_xyz[0]),
                y_m=float(target_xyz[1]),
                z_m=float(target_xyz[2]),
                pitch_deg=float(self.cfg.pitch_deg),
                gripper=float(self.cfg.gripper_open_pwm if gripper is None else gripper),
            )
            self.event_sink.publish_arm_target(msg_target)
        self.event_sink.publish_grasp_event(GraspEventMsg(state=state.name, ok=bool(ok), detail=detail, target=msg_target))

    def update_detection(self, bbox: Optional[BBox]) -> None:
        if bbox is not None:
            self.history.append(bbox)
            if self.state == GraspState.SEARCH:
                self.state = GraspState.CENTERING
                self._emit(self.state, True, "bbox acquired")
        elif self.state in (GraspState.CENTERING, GraspState.DEPTH_LOCK):
            self.state = GraspState.SEARCH
            self.history.clear()
            self.depth_history.clear()
            self.last_lock_debug = None
            self._emit(self.state, False, "bbox lost")

    def try_lock_depth(self, aligned_depth_m: np.ndarray) -> Optional[np.ndarray]:
        box = stable_bbox(list(self.history), self.cfg.max_center_jitter_px, self.cfg.stable_frames)
        if box is None:
            return None
        height, width = aligned_depth_m.shape[:2]
        center_x, center_y = box.center
        if abs(center_x - width / 2.0) > self.cfg.center_tolerance_px or \
                abs(center_y - height / 2.0) > self.cfg.center_tolerance_px:
            self.depth_history.clear()
            return None
        depth = median_depth_in_bbox(aligned_depth_m, box)
        if depth is None:
            self.depth_history.clear()
            return None
        self.depth_history.append(float(depth))
        if len(self.depth_history) < self.cfg.depth_stable_frames:
            return None
        if max(self.depth_history) - min(self.depth_history) > self.cfg.max_depth_jitter_m:
            return None
        depth = float(np.median(np.asarray(self.depth_history, dtype=float)))
        T_base_ee = self.arm.current_ee_matrix_from_last_command()
        dbg = target_pixel_to_base_point_debug(
            box.center,
            depth,
            self.intr,
            T_base_ee,
            self.hand_eye,
            rgb_depth_x_correction_m=self.cfg.rgb_depth_x_correction_m,
        )
        target = np.array(dbg.point_base_m, dtype=float)
        self.last_lock_debug = dbg
        self.locked_target_base = target
        self.state = GraspState.DEPTH_LOCK
        self._emit(self.state, True, f"depth locked: {dbg}", target)
        return target

    def _inside_workspace(self, xyz: np.ndarray) -> bool:
        low = np.asarray(self.cfg.workspace_min_xyz_m, dtype=float)
        high = np.asarray(self.cfg.workspace_max_xyz_m, dtype=float)
        return bool(np.all(xyz >= low) and np.all(xyz <= high))

    def plan_locked_grasp(self):
        if self.locked_target_base is None:
            raise ValueError("no locked target")

        target = self.locked_target_base.copy()
        tool = self.arm.current_ee_matrix_from_last_command()[:3, 3]
        target_delta = target - tool
        target_distance = float(np.linalg.norm(target_delta))
        if target_distance <= self.cfg.pre_grasp_standoff_m + 0.01:
            raise ValueError(f"target too close for pre-grasp standoff: {target_distance:.4f}m")
        approach_axis = target_delta / target_distance
        pre = target - approach_axis * self.cfg.pre_grasp_standoff_m
        grasp = target + approach_axis * self.cfg.grasp_insert_m
        lift = grasp.copy()
        lift[2] += self.cfg.lift_raise_m
        sequence = [
            (GraspState.PRE_GRASP, pre, self.cfg.gripper_open_pwm, self.cfg.pre_grasp_ms),
            (GraspState.APPROACH, grasp, self.cfg.gripper_open_pwm, self.cfg.approach_ms),
            (GraspState.CLOSE, grasp, self.cfg.gripper_close_pwm, self.cfg.gripper_close_ms),
            (GraspState.LIFT, lift, self.cfg.gripper_close_pwm, self.cfg.lift_ms),
        ]
        for state, xyz, gripper, _ in sequence:
            if not self._inside_workspace(xyz):
                raise ValueError(f"{state.name} target outside workspace: {xyz.tolist()}")
            if self.arm.kin.inverse_pose(xyz, pitch_deg=self.cfg.pitch_deg, gripper=0.0) is None:
                raise ValueError(f"{state.name} target has no IK solution: {xyz.tolist()}")
        return sequence

    def _wait_motion(self, duration_ms: int) -> None:
        if not self.arm.adapter.dry_run:
            time.sleep(duration_ms / 1000.0 + self.cfg.motion_settle_s)

    def recover_for_retry(self) -> str:
        """Return to the user-fixed retry pose and clear the stale target lock."""
        self.state = GraspState.RETRY
        values = list(self.cfg.retry_pose_pwms)
        command = self.arm.adapter.send_pwm_command(values, self.cfg.retry_motion_ms)
        self._wait_motion(self.cfg.retry_motion_ms)
        self.history.clear()
        self.depth_history.clear()
        self.locked_target_base = None
        self.last_lock_debug = None
        self.state = GraspState.SEARCH
        self._emit(self.state, True, "retry pose reached; detection reset")
        return command

    def _fail_and_recover(self, reason: str) -> bool:
        self.state = GraspState.FAILED
        self._emit(self.state, False, reason)
        try:
            self.recover_for_retry()
        except Exception as exc:
            self.state = GraspState.FAILED
            self._emit(self.state, False, f"retry recovery failed: {exc}")
        return False

    def execute_locked_grasp(self) -> bool:
        try:
            sequence = self.plan_locked_grasp()
        except ValueError as exc:
            return self._fail_and_recover(str(exc))

        # 005 must be fully open before any arm axis advances toward the bottle.
        self.state = GraspState.OPEN
        self._emit(self.state, True, "opening gripper before approach", gripper=self.cfg.gripper_open_pwm)
        self.arm.adapter.send_partial_pwm_command({5: self.cfg.gripper_open_pwm}, self.cfg.gripper_open_ms)
        self._wait_motion(self.cfg.gripper_open_ms)
        self.arm.adapter.send_stop([5])

        for st, xyz, hand, dur in sequence:
            self.state = st
            self._emit(st, True, "commanding motion", xyz, hand)
            if st == GraspState.CLOSE:
                self.arm.adapter.send_partial_pwm_command({5: self.cfg.gripper_close_pwm}, dur)
                self._wait_motion(dur)
                continue
            res = self.arm.move_xyz(
                xyz,
                pitch_deg=self.cfg.pitch_deg,
                gripper=0.0,
                duration_ms=dur,
                gripper_pwm=hand,
                include_gripper=False,
            )
            if not res.ok:
                print("[GRASP FAILED]", res.reason)
                return self._fail_and_recover(res.reason)
            self._wait_motion(dur)

        # Keep the claw closed while returning to the fixed observation pose.
        self.state = GraspState.RETURN_VERIFY
        verify_pose = list(self.cfg.retry_pose_pwms)
        verify_pose[5] = self.cfg.gripper_close_pwm
        self.arm.adapter.send_pwm_command(verify_pose, self.cfg.retry_motion_ms)
        self._wait_motion(self.cfg.retry_motion_ms)
        self.state = GraspState.VERIFY
        self._emit(self.state, True, "hold closed at retry pose; verify bottle in RGB-D")
        return True
