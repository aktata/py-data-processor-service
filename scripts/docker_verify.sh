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
  && python -m app.cli export_excel --db-path data/output/finance.db --year 2023 --output-path data/output/report.xlsx --json \
  && python -m app.cli export_ppt --db-path data/output/finance.db --year 2023 --output-path data/output/report.pptx --json"

sudo docker image rm "$IMAGE_NAME"

python - <<'PY'
from pathlib import Path
assert Path("data/output/report.xlsx").exists()
assert Path("data/output/report.pptx").exists()
print("✅ docker verify ok")
PY
