#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$PROJECT_ROOT"

VENV_DIR=".venv"
python3 -m venv "$VENV_DIR"

source "$VENV_DIR/bin/activate"

pip install --upgrade pip
pip install -e ".[dev]"

./scripts/lint.sh
./scripts/test.sh

uvicorn app.main:app --host 127.0.0.1 --port 8000 &
SERVER_PID=$!

cleanup() {
  kill "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT

sleep 2

curl -s http://127.0.0.1:8000/health | python - <<'PY'
import json,sys
payload=json.load(sys.stdin)
assert payload["code"]==0
assert payload["data"]["status"]=="ok"
print("/health ok")
PY

curl -s -H "Content-Type: application/json" -d '{"hello":"world","items":[1,2,3]}' \
  http://127.0.0.1:8000/process | python - <<'PY'
import json,sys
payload=json.load(sys.stdin)
assert payload["code"]==0
assert payload["data"]["input_type"]=="json"
print("/process json ok")
PY

