from __future__ import annotations

import re
from datetime import datetime, timezone

from .database_tool import get_connection


def initialize_email_table() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS mock_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                to_email TEXT NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def send_mock_email(prompt: str, sanitized: bool = True) -> dict:
    initialize_email_table()
    match = re.search(r"[\w.+-]+@[\w.-]+\.\w+", prompt)
    to_email = match.group(0) if match else "demo.recipient@example.test"
    body = "This is a safe mock email simulation."
    if not sanitized:
        body = f"Unsafe baseline mock email body copied from prompt: {prompt}"
    created_at = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO mock_emails (to_email, subject, body, status, created_at) VALUES (?, ?, ?, ?, ?)",
            (to_email, "AIC-SAFE mock email", body, "simulated", created_at),
        )
        return {
            "id": cursor.lastrowid,
            "to_email": to_email,
            "subject": "AIC-SAFE mock email",
            "status": "simulated",
            "created_at": created_at,
        }
