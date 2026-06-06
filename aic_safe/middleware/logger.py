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
    "attack_class",
    "tool_intent",
    "risk_level",
    "decision",
    "reason",
    "llm_mode",
    "latency_ms",
    "config_flag_key",
    "output_risk_escalated",
]


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
                    attack_class TEXT NOT NULL,
                    tool_intent TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    llm_mode TEXT NOT NULL,
                    latency_ms INTEGER NOT NULL,
                    config_flag_key TEXT,
                    output_risk_escalated INTEGER NOT NULL
                )
                """
            )

    def write(self, event: dict[str, Any]) -> None:
        event = dict(event)
        event.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        with self.jsonl_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")
        row = {key: event.get(key) for key in SECURITY_EVENT_COLUMNS}
        row["output_risk_escalated"] = int(bool(row["output_risk_escalated"]))
        placeholders = ", ".join("?" for _ in SECURITY_EVENT_COLUMNS)
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.execute(
                f"INSERT OR REPLACE INTO security_events ({', '.join(SECURITY_EVENT_COLUMNS)}) VALUES ({placeholders})",
                [row[key] for key in SECURITY_EVENT_COLUMNS],
            )


def truncate_prompt(prompt: str) -> str:
    if len(prompt) <= config.PROMPT_LOG_MAX_CHARS:
        return prompt
    return prompt[: config.PROMPT_LOG_MAX_CHARS] + "...[truncated]"
