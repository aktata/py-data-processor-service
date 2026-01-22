from __future__ import annotations

import json
import subprocess
from pathlib import Path


def _run(cmd: list[str]) -> dict:
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def test_cli_pipeline(demo_input_dir: Path, tmp_path: Path) -> None:
    db_path = tmp_path / "finance.db"
    output_dir = tmp_path / "output"

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

    export = _run(
        [
            "python",
            "-m",
            "app.cli",
            "export",
            "--db-path",
            str(db_path),
            "--output-dir",
            str(output_dir),
            "--indicator",
            "net_profit_margin",
            "--year",
            "2023",
            "--json",
        ]
    )
    assert export["code"] == 0
    assert (output_dir / "metrics.csv").exists()
    assert (output_dir / "ranking.csv").exists()
    assert (output_dir / "overall_risk.csv").exists()
