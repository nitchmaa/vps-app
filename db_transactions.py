from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path("data/app.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_transactions_table() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_date TEXT NOT NULL,
                amount REAL NOT NULL,
                direction TEXT NOT NULL CHECK (direction IN ('debit', 'credit')),
                merchant TEXT NOT NULL,
                account_last4 TEXT,
                source TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (transaction_date, amount, merchant, direction)
            )
            """
        )


def upsert_transaction(
    transaction_date: str,
    amount: float,
    direction: str,
    merchant: str,
    account_last4: str | None,
    source: str,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO transactions
            (transaction_date, amount, direction, merchant, account_last4, source)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(transaction_date, amount, merchant, direction) DO NOTHING
            """,
            (transaction_date, amount, direction, merchant, account_last4, source),
        )


def fetch_recent_transactions(limit: int = 30) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, transaction_date, amount, direction, merchant, account_last4, source, created_at
            FROM transactions
            ORDER BY transaction_date DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]
