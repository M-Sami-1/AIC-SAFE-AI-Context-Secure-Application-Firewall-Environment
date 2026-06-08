from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import config


SECURITY_EVENT_COLUMNS = [
    "event_id",
    "timestamp",
    "mode",
    "source_label",
    "prompt_id",
    "prompt_text",
    "prompt_safety_label",
    "classifier_output",
    "attack_class",
    "tool_intent",
    "risk_score",
    "risk_level",
    "decision",
    "reason",
    "tool_usage",
    "final_output",
    "attack_success",
    "llm_mode",
    "latency_ms",
    "config_flag_key",
    "output_risk_escalated",
]

SECURITY_EVENT_COLUMN_DEFS = {
    "event_id": "TEXT PRIMARY KEY",
    "timestamp": "TEXT NOT NULL",
    "mode": "TEXT NOT NULL",
    "source_label": "TEXT NOT NULL",
    "prompt_id": "TEXT NOT NULL",
    "prompt_text": "TEXT NOT NULL",
    "prompt_safety_label": "TEXT NOT NULL",
    "classifier_output": "TEXT NOT NULL DEFAULT ''",
    "attack_class": "TEXT NOT NULL",
    "tool_intent": "TEXT NOT NULL",
    "risk_score": "REAL NOT NULL DEFAULT 0",
    "risk_level": "TEXT NOT NULL",
    "decision": "TEXT NOT NULL",
    "reason": "TEXT NOT NULL",
    "tool_usage": "TEXT NOT NULL DEFAULT ''",
    "final_output": "TEXT NOT NULL DEFAULT ''",
    "attack_success": "INTEGER NOT NULL DEFAULT 0",
    "llm_mode": "TEXT NOT NULL",
    "latency_ms": "INTEGER NOT NULL",
    "config_flag_key": "TEXT",
    "output_risk_escalated": "INTEGER NOT NULL",
}


class SecurityLogger:
    def __init__(
        self,
        jsonl_path: Path = config.JSONL_LOG_PATH,
        sqlite_path: Path = config.SECURITY_DB_PATH,
    ) -> None:
        self.jsonl_path = jsonl_path
        self.sqlite_path = sqlite_path
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _initialize(self) -> None:
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS security_events (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    source_label TEXT NOT NULL,
                    prompt_id TEXT NOT NULL,
                    prompt_text TEXT NOT NULL,
                    prompt_safety_label TEXT NOT NULL,
                    classifier_output TEXT NOT NULL DEFAULT '',
                    attack_class TEXT NOT NULL,
                    tool_intent TEXT NOT NULL,
                    risk_score REAL NOT NULL DEFAULT 0,
                    risk_level TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    tool_usage TEXT NOT NULL DEFAULT '',
                    final_output TEXT NOT NULL DEFAULT '',
                    attack_success INTEGER NOT NULL DEFAULT 0,
                    llm_mode TEXT NOT NULL,
                    latency_ms INTEGER NOT NULL,
                    config_flag_key TEXT,
                    output_risk_escalated INTEGER NOT NULL
                )
                """
            )
            existing = {
                row[1]
                for row in conn.execute("PRAGMA table_info(security_events)").fetchall()
            }
            for column in SECURITY_EVENT_COLUMNS:
                if column not in existing:
                    conn.execute(
                        f"ALTER TABLE security_events ADD COLUMN {column} {SECURITY_EVENT_COLUMN_DEFS[column]}"
                    )

    def write(self, event: dict[str, Any]) -> None:
        event = dict(event)
        event.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        with self.jsonl_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")
        row = {key: event.get(key) for key in SECURITY_EVENT_COLUMNS}
        row["output_risk_escalated"] = int(bool(row["output_risk_escalated"]))
        row["attack_success"] = int(bool(row["attack_success"]))
        placeholders = ", ".join("?" for _ in SECURITY_EVENT_COLUMNS)
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.execute(
                f"INSERT INTO security_events ({', '.join(SECURITY_EVENT_COLUMNS)}) VALUES ({placeholders})",
                [row[key] for key in SECURITY_EVENT_COLUMNS],
            )


def truncate_prompt(prompt: str) -> str:
    if len(prompt) <= config.PROMPT_LOG_MAX_CHARS:
        return prompt
    return prompt[: config.PROMPT_LOG_MAX_CHARS] + "...[truncated]"
