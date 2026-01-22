#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$PROJECT_ROOT"

VENV_DIR=".venv"
python3 -m venv "$VENV_DIR"

source "$VENV_DIR/bin/activate"

pip install --upgrade pip
pip install -e ".[dev]"

ruff check .
pytest

python scripts/generate_demo_data.py

python -m app.cli ingest --input-dir data/input --db-path data/output/finance.db --reset --json
python -m app.cli calc --db-path data/output/finance.db --json
python -m app.cli rank --db-path data/output/finance.db --indicator net_profit_margin --year 2023 --n 3 --json
python -m app.cli export --db-path data/output/finance.db --year 2023 --output-dir data/output --json

python - <<'PY'
from pathlib import Path

metrics_path = Path("data/output/metrics.csv")
ranking_path = Path("data/output/ranking.csv")
overall_path = Path("data/output/overall_risk.csv")
assert metrics_path.exists(), "metrics.csv missing"
assert ranking_path.exists(), "ranking.csv missing"
assert overall_path.exists(), "overall_risk.csv missing"
print("✅ verify pipeline ok")
PY
