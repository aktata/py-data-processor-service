#!/usr/bin/env bash
set -euo pipefail

ENV_FILE=".env"
if [[ -f "$ENV_FILE" ]]; then
  export $(grep -v '^#' "$ENV_FILE" | xargs -r)
else
  export $(grep -v '^#' .env.example 2>/dev/null | xargs -r)
fi

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

echo "Starting service on http://$HOST:$PORT"
echo "Docs: http://$HOST:$PORT/docs"

uvicorn app.main:app --host "$HOST" --port "$PORT"
