#!/usr/bin/env python3
"""One-command wrapper to save the current arm pose as tracking startup pose."""

from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from arm_servo_tune import main as tune_main  # noqa: E402


if __name__ == "__main__":
    if "--save-start-pose" not in sys.argv:
        sys.argv.append("--save-start-pose")
    raise SystemExit(tune_main())
