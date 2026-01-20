#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$PROJECT_ROOT"

IMAGE_NAME="data-processor-verify"
CONTAINER_NAME="data-processor-verify-container"

sudo docker build -t "$IMAGE_NAME" .

sudo docker run -d --rm --name "$CONTAINER_NAME" -p 8000:8000 --env-file .env.example "$IMAGE_NAME"

cleanup() {
  sudo docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
}
trap cleanup EXIT

sleep 3

curl -s http://127.0.0.1:8000/health | python - <<'PY'
import json,sys
payload=json.load(sys.stdin)
assert payload["code"]==0
print("/health ok")
PY

curl -s -H "Content-Type: application/json" -d '{"hello":"world","items":[1]}' \
  http://127.0.0.1:8000/process | python - <<'PY'
import json,sys
payload=json.load(sys.stdin)
assert payload["code"]==0
assert payload["data"]["input_type"]=="json"
print("/process ok")
PY

