#!/usr/bin/env bash
set -euo pipefail

STAGE="${1:-help}"
ROOT=/home/orangepi/rk3588_ai/arm_grasp_pipeline
PY=/home/orangepi/rk3588_ai/rknn_lite_env/bin/python3
MODEL=/home/orangepi/rk3588_ai/models/official_yolo11.rknn

cd "$ROOT"
source /home/orangepi/rk3588_ai/scripts/use_realsense_rsusb.sh

run_stage() {
  local stage="$1"
  local run="/home/orangepi/rk3588_ai/debug_logs/dynamic-${stage}-$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$run"
  case "$stage" in
    observe)
      env PYTHONUNBUFFERED=1 "$PY" tools/d435_yolo_grasp.py \
        --model_path "$MODEL" --mode observe --target_class bottle \
        --dry_run false --serial_port /dev/ttyUSB0 --max_frames 30 \
        --save_dir "$run" --metrics_path "$run/events.jsonl" --no_show
      ;;
    center)
      env PYTHONUNBUFFERED=1 "$PY" tools/d435_yolo_grasp.py \
        --model_path "$MODEL" --mode center --target_class bottle \
        --dry_run false --enable_arm --serial_port /dev/ttyUSB0 \
        --center_duration_s 15 --prepare_center_pose true \
        --save_dir "$run" --metrics_path "$run/events.jsonl" --no_show
      ;;
    pregrasp)
      env PYTHONUNBUFFERED=1 "$PY" tools/d435_yolo_grasp.py \
        --model_path "$MODEL" --mode pregrasp --target_class bottle \
        --dry_run false --enable_arm --serial_port /dev/ttyUSB0 \
        --save_dir "$run" --metrics_path "$run/events.jsonl" --no_show
      ;;
    approach)
      env PYTHONUNBUFFERED=1 "$PY" tools/d435_yolo_grasp.py \
        --model_path "$MODEL" --mode approach --closed_loop true \
        --target_class bottle --dry_run false --enable_arm \
        --serial_port /dev/ttyUSB0 --save_dir "$run" \
        --metrics_path "$run/events.jsonl" --no_show
      ;;
    close|lift)
      env PYTHONUNBUFFERED=1 "$PY" tools/d435_yolo_grasp.py \
        --model_path "$MODEL" --mode grasp --max_stage "$stage" \
        --closed_loop true --target_class bottle --dry_run false \
        --enable_arm --serial_port /dev/ttyUSB0 --save_dir "$run" \
        --metrics_path "$run/events.jsonl" --no_show
      ;;
    *)
      echo "internal error: unsupported strict stage $stage" >&2
      return 2
      ;;
  esac
}

case "$STAGE" in
  observe|center|pregrasp|approach|close|lift)
    run_stage "$STAGE"
    ;;
  oneclick)
    # Strict answer-demo path: bounded RGB visual centering, then a completely
    # new dynamic RGB-D/PRAD session through FINAL_ALIGN.  It never closes.
    run_stage center
    run_stage approach
    ;;
  full)
    # Full is intentionally explicit and still obeys all dynamic gates.
    run_stage center
    run_stage lift
    ;;
  *)
    echo "usage: bash tools/run_bottle_stage.sh {observe|center|pregrasp|approach|close|lift|oneclick|full}" >&2
    exit 2
    ;;
esac
