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
python -m app.cli export_excel --db-path data/output/finance.db --year 2023 --output-path data/output/report.xlsx --json
python -m app.cli export_ppt --db-path data/output/finance.db --year 2023 --output-path data/output/report.pptx --json

python - <<'PY'
from pathlib import Path
from pptx import Presentation
from openpyxl import load_workbook

excel_path = Path("data/output/report.xlsx")
ppt_path = Path("data/output/report.pptx")
assert excel_path.exists(), "Excel report missing"
assert ppt_path.exists(), "PPT report missing"

workbook = load_workbook(excel_path)
assert "指标表" in workbook.sheetnames
assert "排名表" in workbook.sheetnames

presentation = Presentation(ppt_path)
assert len(presentation.slides) >= 6
print("✅ verify pipeline ok")
PY
