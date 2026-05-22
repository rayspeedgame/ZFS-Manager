#!/usr/bin/env bash
set -euo pipefail

CONFIG_PATH="${ZFS_MANAGER_CONFIG:-/data/config.json}"
TASK_DB_PATH="${ZFS_MANAGER_TASK_DB:-/data/tasks.sqlite3}"

mkdir -p "$(dirname "$CONFIG_PATH")" "$(dirname "$TASK_DB_PATH")"

if [[ ! -f "$CONFIG_PATH" && -f /app/backend/config/config.example.json ]]; then
  cp /app/backend/config/config.example.json "$CONFIG_PATH"
fi

touch "$TASK_DB_PATH"

shutdown() {
  if [[ -n "${uvicorn_pid:-}" ]] && kill -0 "$uvicorn_pid" 2>/dev/null; then
    kill "$uvicorn_pid" 2>/dev/null || true
  fi

  if [[ -n "${nginx_pid:-}" ]] && kill -0 "$nginx_pid" 2>/dev/null; then
    nginx -s quit 2>/dev/null || kill "$nginx_pid" 2>/dev/null || true
  fi

  wait "${uvicorn_pid:-}" 2>/dev/null || true
  wait "${nginx_pid:-}" 2>/dev/null || true
}

trap shutdown SIGTERM SIGINT

cd /app/backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
uvicorn_pid=$!

nginx -g "daemon off;" &
nginx_pid=$!

set +e
wait -n "$uvicorn_pid" "$nginx_pid"
exit_code=$?
set -e

shutdown
exit "$exit_code"
