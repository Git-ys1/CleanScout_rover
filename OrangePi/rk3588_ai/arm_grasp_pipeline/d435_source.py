# coding: utf-8
"""Backward-compatible D435 import path.

New code should import from realsense_source.py. This file remains so existing
notes/scripts that import arm_grasp_pipeline.d435_source keep working.
"""
from __future__ import annotations

from .realsense_source import D435Source, RealSenseFrame as D435Frame

__all__ = ["D435Source", "D435Frame"]
