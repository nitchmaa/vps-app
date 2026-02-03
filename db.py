from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


DB_PATH = Path("data/app.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_balance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                balance_date TEXT NOT NULL UNIQUE,
                balance REAL NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def upsert_daily_balance(balance_date: str, balance: float) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO daily_balance (balance_date, balance)
            VALUES (?, ?)
            ON CONFLICT(balance_date) DO UPDATE SET
                balance = excluded.balance
            """,
            (balance_date, balance),
        )


def fetch_recent_balances(limit: int = 30) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, balance_date, balance, created_at
            FROM daily_balance
            ORDER BY balance_date DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]
