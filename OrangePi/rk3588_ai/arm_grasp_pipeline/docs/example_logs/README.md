# Hardware-free example logs

- `dry_run_lift.jsonl`: synthetic bottle attached after CLOSE; the dynamic
  state machine reaches `DONE` with `grasp_verified`.
- `simulated_closed_loop_table_failure.jsonl`: synthetic bottle remains on the
  table; the small verification lift classifies `grasp_failed` and blocks the
  full lift.

Both files are generated with `tools/mock_dynamic_grasp_cycle.py`. They contain
fresh frame/PWM pairs and the complete compensation chain; neither opens a
camera nor a serial port.
