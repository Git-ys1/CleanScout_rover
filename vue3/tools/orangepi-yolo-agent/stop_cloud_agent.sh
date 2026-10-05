#!/bin/sh
set -eu
cd "$(dirname "$0")"
pid_file="run/cloud-agent.pid"
if [ ! -f "$pid_file" ]; then
    echo "Cloud Agent 当前未运行。"
    exit 0
fi
agent_pid=$(cat "$pid_file")
if kill -0 "$agent_pid" 2>/dev/null; then kill "$agent_pid"; fi
rm -f "$pid_file"
echo "Cloud Agent 已停止。"
