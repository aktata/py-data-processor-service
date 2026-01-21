from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.ingest.excel_reader import read_company_excel
from app.ingest.normalizer import normalize_statement
from app.storage.repository import ingest_facts


def test_ingest_normalization(demo_input_dir: Path, tmp_path: Path) -> None:
    file_path = demo_input_dir / "Alpha.xlsx"
    sheets = read_company_excel(file_path)
    facts = []
    for statement_type, df in sheets.items():
        facts.append(normalize_statement("Alpha", statement_type, df))

    facts_df = pd.concat(facts, ignore_index=True)
    assert not facts_df.empty
    assert "subject_path" in facts_df.columns

    db_path = tmp_path / "finance.db"
    total = ingest_facts(str(db_path), facts_df)
    assert total == len(facts_df)
