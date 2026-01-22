from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd

from app.analytics.indicators import calculate_indicators
from app.analytics.ranking import top_n_companies
from app.analytics.scoring import apply_scoring, calculate_overall_risk
from app.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.core.logging import generate_trace_id, set_trace_id
from app.core.response import build_error_data, build_response_data
from app.ingest.excel_reader import read_company_excel
from app.ingest.normalizer import normalize_statement
from app.storage.repository import (
    fetch_facts,
    fetch_metrics_df,
    fetch_overall_df,
    ingest_facts,
    query_metrics,
    replace_metrics,
)


def _emit(data: dict[str, Any], json_output: bool) -> None:
    if json_output:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(data, ensure_ascii=False))


def _handle_command(func: Callable[..., dict[str, Any]], json_output: bool, **kwargs: Any) -> int:
    trace_id = generate_trace_id()
    set_trace_id(trace_id)
    try:
        payload = func(**kwargs)
        _emit(build_response_data(payload, trace_id), json_output)
        return 0
    except AppError as exc:
        _emit(build_error_data(exc, trace_id), json_output)
        print(exc.message, file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        error = AppError(
            code=ErrorCode.INTERNAL_ERROR,
            message="Internal error",
            status_code=500,
            details={"error": str(exc)},
        )
        _emit(build_error_data(error, trace_id), json_output)
        print(str(exc), file=sys.stderr)
        return 1


def ingest_command(input_dir: str, db_path: str, reset: bool) -> dict[str, Any]:
    input_path = Path(input_dir)
    if reset and Path(db_path).exists():
        Path(db_path).unlink()

    all_facts = []
    for excel_file in input_path.glob("*.xlsx"):
        company_name = excel_file.stem
        sheets = read_company_excel(excel_file)
        for statement_type, df in sheets.items():
            facts = normalize_statement(company_name, statement_type, df)
            all_facts.append(facts)

    if not all_facts:
        raise AppError(
            code=ErrorCode.INVALID_REQUEST,
            message="No Excel files found for ingestion.",
            status_code=400,
        )

    facts_df = pd.concat(all_facts, ignore_index=True)
    total_rows = ingest_facts(db_path, facts_df)
    return {"ingested_rows": total_rows}


def calc_command(db_path: str, missing_strategy: str) -> dict[str, Any]:
    facts_records = fetch_facts(db_path)
    facts_df = pd.DataFrame(facts_records)
    if facts_df.empty:
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message="No facts found. Run ingest first.",
            status_code=400,
        )

    indicator_result = calculate_indicators(facts_df, missing_value_strategy=missing_strategy)
    scored = apply_scoring(indicator_result.metrics)
    settings = get_settings()
    overall_df = calculate_overall_risk(scored, settings.indicator_weights)
    replace_metrics(db_path, scored, overall_df)
    return {"metrics_rows": len(scored), "warnings": indicator_result.warnings}


def query_command(db_path: str, company: str | None, year: int | None, indicator: str | None) -> dict[str, Any]:
    return {"items": query_metrics(db_path, company, year, indicator)}


def rank_command(db_path: str, indicator: str, year: int, n: int, order: str) -> dict[str, Any]:
    metrics_df = fetch_metrics_df(db_path)
    if metrics_df.empty:
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message="No metrics found. Run calc first.",
            status_code=400,
        )
    ranking_df = top_n_companies(metrics_df, indicator, year, n=n, order=order)
    return {"items": ranking_df.to_dict(orient="records")}


def export_command(
    db_path: str,
    indicator: str,
    year: int,
    n: int,
    order: str,
    output_dir: str,
) -> dict[str, Any]:
    metrics_df = fetch_metrics_df(db_path)
    if metrics_df.empty:
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message="No metrics found. Run calc first.",
            status_code=400,
        )
    ranking_df = top_n_companies(metrics_df, indicator, year, n=n, order=order)
    overall_df = fetch_overall_df(db_path)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    metrics_file = output_path / "metrics.csv"
    ranking_file = output_path / "ranking.csv"
    overall_file = output_path / "overall_risk.csv"

    metrics_df.to_csv(metrics_file, index=False)
    ranking_df.to_csv(ranking_file, index=False)
    overall_df.to_csv(overall_file, index=False)
    return {
        "metrics_path": str(metrics_file),
        "ranking_path": str(ranking_file),
        "overall_path": str(overall_file),
    }


def build_parser() -> argparse.ArgumentParser:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Financial risk analysis CLI")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Ingest Excel files")
    ingest_parser.add_argument("--input-dir", default=settings.input_dir)
    ingest_parser.add_argument("--db-path", default=settings.db_path)
    ingest_parser.add_argument("--reset", action="store_true")

    calc_parser = subparsers.add_parser("calc", help="Calculate indicators and risk")
    calc_parser.add_argument("--db-path", default=settings.db_path)
    calc_parser.add_argument("--missing-strategy", default=settings.missing_value_strategy)

    query_parser = subparsers.add_parser("query", help="Query metrics")
    query_parser.add_argument("--db-path", default=settings.db_path)
    query_parser.add_argument("--company")
    query_parser.add_argument("--year", type=int)
    query_parser.add_argument("--indicator")

    rank_parser = subparsers.add_parser("rank", help="Rank companies by indicator")
    rank_parser.add_argument("--db-path", default=settings.db_path)
    rank_parser.add_argument("--indicator", required=True)
    rank_parser.add_argument("--year", type=int, required=True)
    rank_parser.add_argument("--n", type=int, default=5)
    rank_parser.add_argument("--order", default="desc", choices=["desc", "asc"])

    export_parser = subparsers.add_parser("export", help="Export CSV summaries")
    export_parser.add_argument("--db-path", default=settings.db_path)
    export_parser.add_argument("--output-dir", default=settings.output_dir)
    export_parser.add_argument("--indicator", default="net_profit_margin")
    export_parser.add_argument("--year", type=int, required=True)
    export_parser.add_argument("--n", type=int, default=5)
    export_parser.add_argument("--order", default="desc", choices=["desc", "asc"])

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    json_output = args.json

    if args.command == "ingest":
        return _handle_command(
            ingest_command,
            json_output,
            input_dir=args.input_dir,
            db_path=args.db_path,
            reset=args.reset,
        )

    if args.command == "calc":
        return _handle_command(
            calc_command,
            json_output,
            db_path=args.db_path,
            missing_strategy=args.missing_strategy,
        )

    if args.command == "query":
        return _handle_command(
            query_command,
            json_output,
            db_path=args.db_path,
            company=args.company,
            year=args.year,
            indicator=args.indicator,
        )

    if args.command == "rank":
        return _handle_command(
            rank_command,
            json_output,
            db_path=args.db_path,
            indicator=args.indicator,
            year=args.year,
            n=args.n,
            order=args.order,
        )

    if args.command == "export":
        return _handle_command(
            export_command,
            json_output,
            db_path=args.db_path,
            output_dir=args.output_dir,
            indicator=args.indicator,
            year=args.year,
            n=args.n,
            order=args.order,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
