#!/usr/bin/env python3
"""Hardware-free full dynamic state-machine exercise with synthetic RGB-D."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.grasp_state_machine import (  # noqa: E402
    DynamicGraspStateMachine,
    JsonlGraspLogger,
)
from arm_grasp_pipeline.tests.dynamic_fakes import (  # noqa: E402
    StaticTargetSource,
    runtime_parts,
)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-stage",
        choices=("pregrasp", "approach", "close", "lift"),
        default="lift",
    )
    parser.add_argument(
        "--object-behavior",
        choices=("held", "table", "lost_after_pregrasp"),
        default="held",
    )
    parser.add_argument("--metrics-path", default="")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    config, frames, kin, adapter, arm, target = runtime_parts()
    source_options = {
        "attach_on_close": args.object_behavior == "held",
        "fail_call": 3 if args.object_behavior == "lost_after_pregrasp" else None,
    }
    source = StaticTargetSource(adapter, kin, frames, target, **source_options)
    logger = JsonlGraspLogger(args.metrics_path or None)
    machine = DynamicGraspStateMachine(
        arm, frames, config, logger=logger, allow_motion=True
    )
    try:
        outcome = machine.run_to_stage(source, args.max_stage)
    finally:
        logger.close()
    print("MOCK_DYNAMIC_SUMMARY " + json.dumps(asdict(outcome), default=str))
    # A requested happy path must never mask an internal failure with exit 0.
    expected_failure = bool(
        (
            args.object_behavior == "lost_after_pregrasp"
            # PRE_GRASP includes the mandatory post-motion reacquisition, so
            # losing the target there is already an expected fail-closed case.
            and args.max_stage in ("pregrasp", "approach", "close", "lift")
        )
        or (
            args.object_behavior == "table"
            and args.max_stage in ("close", "lift")
        )
    )
    expected_success = not expected_failure
    if expected_success and not outcome.ok:
        return 2
    if not expected_success and outcome.ok:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
