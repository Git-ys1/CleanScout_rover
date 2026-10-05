#!/bin/sh
set -eu
cd "$(dirname "$0")"
mkdir -p logs run
pid_file="run/cloud-agent.pid"
if [ -f "$pid_file" ] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
    echo "Cloud Agent 已在运行，PID: $(cat "$pid_file")"
    exit 0
fi
test -x .venv/bin/python || { echo "缺少 .venv，请先运行 ./setup.sh"; exit 1; }
test -f .cloud-agent.json || { echo "缺少 .cloud-agent.json"; exit 1; }
test -f .cloud-agent-token || { echo "缺少 .cloud-agent-token"; exit 1; }
nohup .venv/bin/python -B cloud_agent.py >>logs/cloud-agent.log 2>&1 &
agent_pid=$!
echo "$agent_pid" >"$pid_file"
sleep 2
if ! kill -0 "$agent_pid" 2>/dev/null; then
    tail -n 40 logs/cloud-agent.log
    rm -f "$pid_file"
    exit 1
fi
echo "Cloud Agent 已启动，PID: $agent_pid"
