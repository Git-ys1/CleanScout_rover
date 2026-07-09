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
from typing import Optional, Tuple

import numpy as np

from .arm_motion import ArmMotion
from .geometry import CameraIntrinsics, HandEye, target_pixel_to_base_point_debug
from .ros_compat import ArmTargetMsg, GraspEventMsg, GraspEventSink, NullRosBridge
from .target_depth import BBox, median_depth_in_bbox, stable_bbox


class GraspState(Enum):
    SEARCH = auto()
    CENTERING = auto()
    DEPTH_LOCK = auto()
    PRE_GRASP = auto()
    DESCEND = auto()
    CLOSE = auto()
    LIFT = auto()
    PLACE = auto()
    RELEASE = auto()
    HOME = auto()
    FAILED = auto()


@dataclass
class GraspConfig:
    stable_frames: int = 5
    max_center_jitter_px: float = 10.0
    pre_grasp_dz_m: float = 0.055
    descend_dz_m: float = 0.005
    lift_z_m: float = 0.18
    pitch_deg: float = 70.0
    open_gripper: float = 0.80
    close_gripper: float = -0.020
    place_xyz_m: Tuple[float, float, float] = (0.16, -0.12, 0.12)
    home_xyz_m: Tuple[float, float, float] = (0.16, 0.00, 0.16)
    rgb_depth_x_correction_m: float = -0.007


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
        self.locked_target_base: Optional[np.ndarray] = None

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
                gripper=float(self.cfg.open_gripper if gripper is None else gripper),
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
            self._emit(self.state, False, "bbox lost")

    def try_lock_depth(self, aligned_depth_m: np.ndarray) -> Optional[np.ndarray]:
        box = stable_bbox(list(self.history), self.cfg.max_center_jitter_px, self.cfg.stable_frames)
        if box is None:
            return None
        depth = median_depth_in_bbox(aligned_depth_m, box)
        if depth is None:
            return None
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
        self.locked_target_base = target
        self.state = GraspState.DEPTH_LOCK
        self._emit(self.state, True, f"depth locked: {dbg}", target)
        return target

    def execute_locked_grasp(self) -> bool:
        if self.locked_target_base is None:
            self.state = GraspState.FAILED
            self._emit(self.state, False, "no locked target")
            return False

        target = self.locked_target_base.copy()
        pre = target.copy(); pre[2] += self.cfg.pre_grasp_dz_m
        down = target.copy(); down[2] += self.cfg.descend_dz_m
        lift = down.copy(); lift[2] = max(lift[2] + 0.08, self.cfg.lift_z_m)

        sequence = [
            (GraspState.PRE_GRASP, pre, self.cfg.open_gripper, 900),
            (GraspState.DESCEND, down, self.cfg.open_gripper, 900),
            (GraspState.CLOSE, down, self.cfg.close_gripper, 500),
            (GraspState.LIFT, lift, self.cfg.close_gripper, 900),
            (GraspState.PLACE, np.array(self.cfg.place_xyz_m, dtype=float), self.cfg.close_gripper, 1200),
            (GraspState.RELEASE, np.array(self.cfg.place_xyz_m, dtype=float), self.cfg.open_gripper, 500),
            (GraspState.HOME, np.array(self.cfg.home_xyz_m, dtype=float), self.cfg.open_gripper, 1000),
        ]
        for st, xyz, hand, dur in sequence:
            self.state = st
            self._emit(st, True, "commanding motion", xyz, hand)
            res = self.arm.move_xyz(xyz, pitch_deg=self.cfg.pitch_deg, gripper=hand, duration_ms=dur)
            if not res.ok:
                print("[GRASP FAILED]", res.reason)
                self.state = GraspState.FAILED
                self._emit(self.state, False, res.reason, xyz, hand)
                return False
        self.state = GraspState.SEARCH
        self.history.clear()
        self.locked_target_base = None
        self._emit(self.state, True, "cycle complete")
        return True
