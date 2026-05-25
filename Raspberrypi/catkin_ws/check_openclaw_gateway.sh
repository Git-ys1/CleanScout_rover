#!/usr/bin/env bash
set -e

echo "[openclaw] PATH=$PATH"
echo

echo "[openclaw] command lookup"
command -v openclaw || true
echo

echo "[openclaw] symlink target"
ls -l "$HOME/.npm-global/bin/openclaw" || true
echo

echo "[openclaw] version"
node -v || true
echo

echo "[openclaw] user service file"
ls -l "$HOME/.config/systemd/user/openclaw-gateway.service" || true
echo

echo "[openclaw] config file"
ls -l "$HOME/.openclaw/openclaw.json" || true
echo

echo "[openclaw] gateway port"
ss -lntp | grep 18789 || true
echo

echo "[openclaw] curl models"
curl -sS -H "Authorization: Bearer $(python3 - <<'PY'
import json, pathlib
p = pathlib.Path.home() / '.openclaw' / 'openclaw.json'
if p.exists():
    cfg = json.loads(p.read_text())
    print(cfg.get('gateway', {}).get('auth', {}).get('token', ''))
PY
)" http://127.0.0.1:18789/v1/models || true
