from __future__ import annotations

import sqlite3
from pathlib import Path


def get_connection(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS financial_facts (
            company_name TEXT NOT NULL,
            statement_type TEXT NOT NULL,
            category TEXT,
            subject_path TEXT NOT NULL,
            subject_l1 TEXT,
            subject_l2 TEXT,
            subject_l3 TEXT,
            year INTEGER NOT NULL,
            amount REAL NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS metrics_table (
            company_name TEXT NOT NULL,
            year INTEGER NOT NULL,
            indicator_name TEXT NOT NULL,
            indicator_value REAL,
            risk_level TEXT,
            risk_score REAL,
            details TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS overall_risk (
            company_name TEXT NOT NULL,
            year INTEGER NOT NULL,
            overall_risk_score REAL
        )
        """
    )
    conn.commit()
