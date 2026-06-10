#!/usr/bin/env bash
set -euo pipefail

TARGET_ROOT="${1:-$HOME/rk3588_ai}"
MODEL_ZOO="$TARGET_ROOT/rknn_model_zoo"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
OVERLAY_DIR="$BASE_DIR/model_zoo_overlay"
UPSTREAM_URL="https://github.com/airockchip/rknn_model_zoo.git"
UPSTREAM_COMMIT="bad6c73"

mkdir -p "$TARGET_ROOT"

if [ ! -d "$MODEL_ZOO/.git" ]; then
  git clone "$UPSTREAM_URL" "$MODEL_ZOO"
fi

git -C "$MODEL_ZOO" fetch --tags origin
git -C "$MODEL_ZOO" checkout "$UPSTREAM_COMMIT"

cp -av \
  "$OVERLAY_DIR/examples/yolo11/python/yolo11.py" \
  "$MODEL_ZOO/examples/yolo11/python/yolo11.py"

cp -av \
  "$OVERLAY_DIR/examples/yolo11/python/yolo11_camera.py" \
  "$MODEL_ZOO/examples/yolo11/python/yolo11_camera.py"

echo "Applied CleanScout OrangePi overlay to $MODEL_ZOO"
