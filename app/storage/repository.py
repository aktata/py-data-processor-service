from __future__ import annotations

import json
from typing import Any

import pandas as pd

from app.storage.db import get_connection, init_db


def ingest_facts(db_path: str, facts: pd.DataFrame) -> int:
    with get_connection(db_path) as conn:
        init_db(conn)
        facts.to_sql("financial_facts", conn, if_exists="append", index=False)
    return len(facts)


def replace_metrics(db_path: str, metrics: pd.DataFrame, overall: pd.DataFrame) -> None:
    with get_connection(db_path) as conn:
        init_db(conn)
        conn.execute("DELETE FROM metrics_table")
        conn.execute("DELETE FROM overall_risk")
        metrics.to_sql("metrics_table", conn, if_exists="append", index=False)
        overall.to_sql("overall_risk", conn, if_exists="append", index=False)


def query_metrics(
    db_path: str,
    company: str | None = None,
    year: int | None = None,
    indicator: str | None = None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if company:
        clauses.append("company_name = ?")
        params.append(company)
    if year is not None:
        clauses.append("year = ?")
        params.append(year)
    if indicator:
        clauses.append("indicator_name = ?")
        params.append(indicator)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = f"SELECT * FROM metrics_table {where} ORDER BY company_name, year"

    with get_connection(db_path) as conn:
        init_db(conn)
        rows = conn.execute(query, params).fetchall()
    results: list[dict[str, Any]] = []
    for row in rows:
        record = dict(row)
        if record.get("details"):
            record["details"] = json.loads(record["details"])
        results.append(record)
    return results


def fetch_facts(
    db_path: str,
    company: str | None = None,
    year: int | None = None,
    statement_type: str | None = None,
    subject_prefix: str | None = None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if company:
        clauses.append("company_name = ?")
        params.append(company)
    if year is not None:
        clauses.append("year = ?")
        params.append(year)
    if statement_type:
        clauses.append("statement_type = ?")
        params.append(statement_type)
    if subject_prefix:
        clauses.append("subject_path LIKE ?")
        params.append(f"{subject_prefix}%")

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = f"SELECT * FROM financial_facts {where} ORDER BY subject_path"

    with get_connection(db_path) as conn:
        init_db(conn)
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def fetch_companies(db_path: str) -> list[str]:
    with get_connection(db_path) as conn:
        init_db(conn)
        rows = conn.execute("SELECT DISTINCT company_name FROM financial_facts").fetchall()
    return [row[0] for row in rows]


def fetch_years(db_path: str) -> list[int]:
    with get_connection(db_path) as conn:
        init_db(conn)
        rows = conn.execute("SELECT DISTINCT year FROM financial_facts ORDER BY year").fetchall()
    return [row[0] for row in rows]


def fetch_metrics_df(db_path: str) -> pd.DataFrame:
    with get_connection(db_path) as conn:
        init_db(conn)
        return pd.read_sql_query("SELECT * FROM metrics_table", conn)


def fetch_overall_df(db_path: str) -> pd.DataFrame:
    with get_connection(db_path) as conn:
        init_db(conn)
        return pd.read_sql_query("SELECT * FROM overall_risk", conn)
