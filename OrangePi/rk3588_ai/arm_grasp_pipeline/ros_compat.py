# coding: utf-8
"""ROS-ready boundary objects for the non-ROS OrangePi grasp pipeline.

This module intentionally has no rclpy/rospy import.  The pipeline calls this
interface with plain dataclasses.  When ROS is reintroduced, add a small adapter
that converts these events to ROS2/ROS1 messages without rewriting IK, geometry,
or grasp state code.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class ArmTargetMsg:
    frame_id: str
    x_m: float
    y_m: float
    z_m: float
    pitch_deg: float
    gripper: float
    source: str = "orange_pi_non_ros"


@dataclass(frozen=True)
class GraspEventMsg:
    state: str
    ok: bool
    detail: str = ""
    target: Optional[ArmTargetMsg] = None


class GraspEventSink(object):
    """Minimal duck-typed event sink interface.

    Do not use typing.Protocol here: the development PC may run Python 3.7,
    while the OrangePi baseline is Python 3.8. A plain base class keeps the
    non-ROS boundary importable everywhere.
    """

    def publish_grasp_event(self, event: GraspEventMsg) -> None:
        raise NotImplementedError

    def publish_arm_target(self, target: ArmTargetMsg) -> None:
        raise NotImplementedError


class NullRosBridge:
    """Default bridge for current non-ROS development stage."""
    def publish_grasp_event(self, event: GraspEventMsg) -> None:
        return None

    def publish_arm_target(self, target: ArmTargetMsg) -> None:
        return None


class PrintRosBridge:
    """Debug bridge: prints ROS-boundary payloads as dictionaries."""
    def publish_grasp_event(self, event: GraspEventMsg) -> None:
        print("[ROS-COMPAT grasp_event]", asdict(event))

    def publish_arm_target(self, target: ArmTargetMsg) -> None:
        print("[ROS-COMPAT arm_target]", asdict(target))


def to_plain_dict(obj: Any):
    return asdict(obj)
