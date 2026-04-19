#!/usr/bin/env bash
set -euo pipefail

pkill -9 -f edge_relay.py || true
pkill -9 -f c324_edge_relay || true

sleep 1

ps -ef | grep -E 'edge_relay.py|c324_edge_relay' | grep -v grep || true
