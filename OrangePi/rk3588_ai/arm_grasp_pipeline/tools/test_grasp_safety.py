#!/usr/bin/env python3
"""Hardware-free checks for the dynamic grasp state machine safety gates."""
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from arm_grasp_pipeline.grasp_state_machine import (  # noqa: E402
    DynamicGraspStateMachine,
    GraspState,
)
from arm_grasp_pipeline.tests.dynamic_fakes import (  # noqa: E402
    StaticTargetSource,
    runtime_parts,
)


def make_machine(**source_kwargs):
    config, frames, kin, adapter, arm, target = runtime_parts()
    source = StaticTargetSource(
        adapter, kin, frames, target, **source_kwargs
    )
    machine = DynamicGraspStateMachine(
        arm, frames, config, allow_motion=True
    )
    return machine, source, adapter


def motion_labels(machine):
    return [
        row.get("motion_label")
        for row in machine.logger.records
        if row.get("motion_label")
    ]


def main() -> int:
    pregrasp, source, adapter = make_machine()
    outcome = pregrasp.run_to_stage(source, "pregrasp")
    assert outcome.ok, outcome.reason
    assert outcome.state == GraspState.DONE
    assert outcome.commands_executed == 2
    assert motion_labels(pregrasp) == ["OPEN", "MOVE_PREGRASP"]
    assert len(source.calls) >= 3
    assert adapter._ser is None

    approach, source, adapter = make_machine()
    outcome = approach.run_to_stage(source, "approach")
    assert outcome.ok, outcome.reason
    assert outcome.approach_iterations > 1
    planned_steps = [
        row["planned_step_xyz"]
        for row in approach.logger.records
        if row.get("state") == "FINE_APPROACH"
        and "planned_step_xyz" in row
    ]
    assert len(planned_steps) == outcome.approach_iterations
    for step in planned_steps:
        length = math.sqrt(sum(float(value) ** 2 for value in step))
        assert 0.005 - 1e-12 <= length <= 0.010 + 1e-12
    assert adapter._ser is None

    invalid_depth, source, _ = make_machine(depth_override_m=0.16)
    outcome = invalid_depth.run_to_stage(source, "pregrasp")
    assert not outcome.ok
    assert "unreliable zone" in outcome.reason
    assert outcome.commands_executed == 0

    target_loss, source, _ = make_machine(fail_call=3)
    outcome = target_loss.run_to_stage(source, "approach")
    assert not outcome.ok
    assert "target lost" in outcome.reason
    assert outcome.commands_executed == 2
    assert outcome.approach_iterations == 0

    table_object, source, _ = make_machine(attach_on_close=False)
    outcome = table_object.run_to_stage(source, "lift")
    assert not outcome.ok
    assert outcome.grasp_verification == "grasp_failed"
    assert "VERIFY_LIFT" in motion_labels(table_object)
    assert "LIFT" not in motion_labels(table_object)

    held_object, source, adapter = make_machine(attach_on_close=True)
    outcome = held_object.run_to_stage(source, "lift")
    assert outcome.ok, outcome.reason
    assert outcome.grasp_verification == "grasp_verified"
    labels = motion_labels(held_object)
    assert labels.index("VERIFY_LIFT") < labels.index("LIFT")
    assert adapter._ser is None

    print("GRASP_SAFETY_CHECK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
