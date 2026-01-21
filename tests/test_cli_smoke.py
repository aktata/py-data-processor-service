from __future__ import annotations

import json
import subprocess
from pathlib import Path


def _run(cmd: list[str]) -> dict:
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def test_cli_pipeline(demo_input_dir: Path, tmp_path: Path) -> None:
    db_path = tmp_path / "finance.db"

    ingest = _run(
        [
            "python",
            "-m",
            "app.cli",
            "ingest",
            "--input-dir",
            str(demo_input_dir),
            "--db-path",
            str(db_path),
            "--reset",
            "--json",
        ]
    )
    assert ingest["code"] == 0

    calc = _run(
        [
            "python",
            "-m",
            "app.cli",
            "calc",
            "--db-path",
            str(db_path),
            "--json",
        ]
    )
    assert calc["code"] == 0
