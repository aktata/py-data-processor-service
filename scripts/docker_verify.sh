#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$PROJECT_ROOT"

IMAGE_NAME="financial-risk-service:verify"

sudo docker build -t "$IMAGE_NAME" .

sudo docker run --rm \
  -v "$PROJECT_ROOT/data:/app/data" \
  "$IMAGE_NAME" \
  /bin/bash -c "python scripts/generate_demo_data.py \
  && python -m app.cli ingest --input-dir data/input --db-path data/output/finance.db --reset --json \
  && python -m app.cli calc --db-path data/output/finance.db --json \
  && python -m app.cli export --db-path data/output/finance.db --year 2023 --output-dir data/output --json"

sudo docker image rm "$IMAGE_NAME"

python - <<'PY'
from pathlib import Path
assert Path("data/output/metrics.csv").exists()
assert Path("data/output/ranking.csv").exists()
assert Path("data/output/overall_risk.csv").exists()
print("✅ docker verify ok")
PY
