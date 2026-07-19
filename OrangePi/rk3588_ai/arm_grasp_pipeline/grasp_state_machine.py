# coding: utf-8
"""Fixed-view YOLO + aligned D435 depth grasp state machine."""
from __future__ import annotations

from collections import deque
import json
import time
from typing import Optional

import numpy as np

from .arm_motion import ArmMotion
from .fixed_view import (
    REQUIRED_WRIST_PWM,
    FixedViewTargetDebug,
    ObjectGeometry,
    fixed_view_target_debug,
)
from .geometry import CameraIntrinsics, validate_rigid_transform
from .grasp_planner import (
    GraspConfig,
    GraspPlanStep,
    GraspState,
    build_fixed_view_grasp_plan,
    inside_workspace,
    stage_reached,
)
from .ros_compat import ArmTargetMsg, GraspEventMsg, GraspEventSink, NullRosBridge
from .target_depth import BBox, median_depth_in_bbox, stable_bbox


class GraspStateMachine:
    def __init__(self, arm: ArmMotion, intr: CameraIntrinsics,
                 T_base_camera_reference, cfg: Optional[GraspConfig] = None,
                 object_geometry: Optional[ObjectGeometry] = None,
                 event_sink: Optional[GraspEventSink] = None) -> None:
        self.arm = arm
        self.intr = intr
        self.cfg = cfg or GraspConfig()
        self.T_base_camera_reference = validate_rigid_transform(
            T_base_camera_reference, "T_base_camera_reference"
        )
        if object_geometry is None:
            raise ValueError("fixed-view state machine requires object_geometry from config")
        self.object_geometry = object_geometry
        self.event_sink = event_sink or NullRosBridge()
        self.state = GraspState.SEARCH
        self.history = deque(maxlen=max(10, self.cfg.stable_frames + 2))
        self.depth_history = deque(maxlen=max(3, self.cfg.depth_stable_frames))
        self.locked_target_base = None
        self.last_lock_debug: Optional[FixedViewTargetDebug] = None

    def _emit(self, state: GraspState, ok: bool, detail="", target_xyz=None,
              gripper=None, pitch_deg=None) -> None:
        msg_target = None
        if target_xyz is not None:
            msg_target = ArmTargetMsg(
                frame_id="arm_base",
                x_m=float(target_xyz[0]),
                y_m=float(target_xyz[1]),
                z_m=float(target_xyz[2]),
                pitch_deg=float(self.cfg.pitch_deg if pitch_deg is None else pitch_deg),
                gripper=float(self.cfg.gripper_open_pwm if gripper is None else gripper),
            )
            self.event_sink.publish_arm_target(msg_target)
        self.event_sink.publish_grasp_event(
            GraspEventMsg(state=state.name, ok=bool(ok), detail=detail, target=msg_target)
        )

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

    def try_lock_depth(self, aligned_depth_m: np.ndarray):
        """Lock a stable bottle center in base coordinates from aligned RGB-D."""
        box = stable_bbox(
            list(self.history), self.cfg.max_center_jitter_px, self.cfg.stable_frames
        )
        if box is None:
            return None
        depth = median_depth_in_bbox(
            aligned_depth_m, box, inner_ratio=self.cfg.depth_roi_inner_ratio
        )
        if depth is None:
            self.depth_history.clear()
            return None
        self.depth_history.append(float(depth))
        if len(self.depth_history) < self.cfg.depth_stable_frames:
            return None
        if max(self.depth_history) - min(self.depth_history) > self.cfg.max_depth_jitter_m:
            return None

        depth = float(np.median(np.asarray(self.depth_history, dtype=float)))
        debug = fixed_view_target_debug(
            box.center,
            depth,
            self.intr,
            self.T_base_camera_reference,
            self.object_geometry,
        )
        target = np.asarray(debug.bottle_center_base_m, dtype=float)
        self.last_lock_debug = debug
        self.locked_target_base = target
        self.state = GraspState.DEPTH_LOCK
        self._emit(self.state, True, "fixed-view depth locked", target)
        return target.copy()

    def _inside_workspace(self, xyz) -> bool:
        return inside_workspace(xyz, self.cfg)

    def plan_locked_grasp(self, max_stage=None):
        if self.locked_target_base is None:
            raise ValueError("no locked target")
        return build_fixed_view_grasp_plan(
            self.locked_target_base, self.arm.kin, self.cfg, max_stage=max_stage
        )

    def _wait_motion(self, duration_ms) -> None:
        if not self.arm.adapter.dry_run:
            time.sleep(float(duration_ms) / 1000.0 + self.cfg.motion_settle_s)

    def recover_for_retry(self) -> str:
        self.state = GraspState.RETRY
        values = list(self.cfg.retry_pose_pwms)
        if len(values) != 6 or values[4] != REQUIRED_WRIST_PWM:
            raise ValueError("retry pose must keep Servo004 at PWM {}".format(
                REQUIRED_WRIST_PWM
            ))
        command = self.arm.adapter.send_pwm_command(values, self.cfg.retry_motion_ms)
        self._wait_motion(self.cfg.retry_motion_ms)
        self.history.clear()
        self.depth_history.clear()
        self.locked_target_base = None
        self.last_lock_debug = None
        self.state = GraspState.SEARCH
        self._emit(self.state, True, "fixed reference pose reached; detection reset")
        return command

    def _fail(self, reason) -> bool:
        self.state = GraspState.FAILED
        self._emit(self.state, False, str(reason))
        print("[GRASP FAILED] {}".format(reason))
        return False

    @staticmethod
    def _print_step(step: GraspPlanStep) -> None:
        print("GRASP_STAGE_PREFLIGHT " + json.dumps(step.as_dict(), ensure_ascii=False))

    def execute_locked_grasp(self, max_stage="LIFT") -> bool:
        max_stage = str(max_stage).strip().upper()
        allowed_stages = {"OPEN", "PRE_GRASP", "APPROACH", "CLOSE", "LIFT"}
        if max_stage not in allowed_stages:
            raise ValueError("max_stage must be one of {}".format(sorted(allowed_stages)))
        try:
            sequence = self.plan_locked_grasp(max_stage=max_stage)
        except ValueError as exc:
            return self._fail(exc)

        self.state = GraspState.WRIST_LOCK
        self._emit(
            self.state, True,
            "locking Servo004 at calibrated PWM {}".format(REQUIRED_WRIST_PWM),
        )
        self.arm.adapter.send_partial_pwm_command(
            {4: REQUIRED_WRIST_PWM}, self.cfg.wrist_lock_ms
        )
        self._wait_motion(self.cfg.wrist_lock_ms)

        for index, step in enumerate(sequence):
            next_state = sequence[index + 1].state if index + 1 < len(sequence) else None
            self.state = step.state
            self._print_step(step)
            self._emit(
                step.state,
                True,
                "preflight passed; commanding stage",
                None if step.xyz_m is None else np.asarray(step.xyz_m, dtype=float),
                step.gripper_pwm,
                step.pitch_deg,
            )

            if step.state == GraspState.OPEN:
                self.arm.adapter.send_partial_pwm_command(
                    {5: step.gripper_pwm}, step.duration_ms
                )
            elif step.state == GraspState.CLOSE:
                self.arm.adapter.send_partial_pwm_command(
                    {5: step.gripper_pwm}, step.duration_ms
                )
            else:
                result = self.arm.execute_ik(step.ik, step.duration_ms)
                if not result.ok:
                    return self._fail(result.reason)
            self._wait_motion(step.duration_ms)

            if stage_reached(step.state, next_state, max_stage):
                self.state = GraspState.VERIFY
                self._emit(
                    self.state,
                    True,
                    "{} stage complete; holding for inspection".format(max_stage),
                )
                return True

        self.state = GraspState.VERIFY
        self._emit(self.state, True, "LIFT complete; holding the current pose")
        return True
