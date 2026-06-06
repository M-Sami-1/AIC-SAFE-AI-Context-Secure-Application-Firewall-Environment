from __future__ import annotations

import sqlite3
from pathlib import Path

import config


def get_connection(path: Path = config.APP_DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                department TEXT NOT NULL,
                salary INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                account_status TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS secrets (
                id INTEGER PRIMARY KEY,
                secret_name TEXT NOT NULL,
                secret_value TEXT NOT NULL,
                environment TEXT NOT NULL
            );
            """
        )
        if conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO employees VALUES (?, ?, ?, ?, ?)",
                [
                    (1, "Avery Chen", "avery.chen@example.test", "Engineering", 128000),
                    (2, "Mina Patel", "mina.patel@example.test", "Security", 141000),
                    (3, "Jordan Lee", "jordan.lee@example.test", "Finance", 118500),
                ],
            )
        if conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO customers VALUES (?, ?, ?, ?, ?)",
                [
                    (1, "Alex Rivera", "alex.customer@example.test", "555-010-2200", "active"),
                    (2, "Sam Morgan", "sam.customer@example.test", "555-010-2201", "trial"),
                    (3, "Taylor Brooks", "taylor.customer@example.test", "555-010-2202", "paused"),
                ],
            )
        if conn.execute("SELECT COUNT(*) FROM secrets").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO secrets VALUES (?, ?, ?, ?)",
                [
                    (1, "demo_api_key", "AICSAFE_DEMO_KEY_123456", "local"),
                    (2, "mock_webhook_token", "token_DEMO_ONLY_7890", "local"),
                ],
            )


def read_business_data(sanitized: bool = True) -> list[dict]:
    initialize_database()
    with get_connection() as conn:
        if sanitized:
            rows = conn.execute(
                "SELECT id, name, department FROM employees ORDER BY id LIMIT 5"
            ).fetchall()
            return [dict(row) for row in rows]
        employees = [dict(row) for row in conn.execute("SELECT * FROM employees").fetchall()]
        customers = [dict(row) for row in conn.execute("SELECT * FROM customers").fetchall()]
        secrets = [dict(row) for row in conn.execute("SELECT * FROM secrets").fetchall()]
        return [{"employees": employees, "customers": customers, "secrets": secrets}]
