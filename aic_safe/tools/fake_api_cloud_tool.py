from __future__ import annotations

from datetime import datetime, timezone

from .database_tool import get_connection


def initialize_fake_cloud_table() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS fake_cloud_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_name TEXT NOT NULL,
                target TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def run_fake_cloud_action(prompt: str, sanitized: bool = True) -> dict:
    initialize_fake_cloud_table()
    lower = prompt.lower()
    if "s3" in lower or "upload" in lower:
        action_name = "mock_s3_upload"
    elif "webhook" in lower:
        action_name = "mock_webhook_trigger"
    else:
        action_name = "mock_cloud_function_invocation"
    target = "safe-demo-target" if sanitized else "unsafe-baseline-target"
    created_at = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO fake_cloud_actions (action_name, target, status, created_at) VALUES (?, ?, ?, ?)",
            (action_name, target, "simulated", created_at),
        )
    return {
        "id": cursor.lastrowid,
        "action_name": action_name,
        "target": target,
        "status": "simulated",
        "created_at": created_at,
    }
