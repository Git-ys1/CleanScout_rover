#!/usr/bin/env python3
"""Compatibility entry point for the hardware-free dynamic grasp mock."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.tools.mock_dynamic_grasp_cycle import (  # noqa: E402
    main as dynamic_main,
)


def main(argv=None) -> int:
    forwarded = list(sys.argv[1:] if argv is None else argv)
    if "--print_ros" in forwarded:
        forwarded = [value for value in forwarded if value != "--print_ros"]
        print(
            "MOCK_GRASP_CYCLE_COMPAT print_ros_ignored=true "
            "reason=dynamic_mock_uses_JSON_summary"
        )
    print("MOCK_GRASP_CYCLE_COMPAT backend=mock_dynamic_grasp_cycle")
    return dynamic_main(forwarded)


if __name__ == "__main__":
    raise SystemExit(main())
