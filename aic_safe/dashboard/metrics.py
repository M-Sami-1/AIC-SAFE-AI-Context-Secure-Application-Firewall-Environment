from __future__ import annotations

import sqlite3
from pathlib import Path

import config


def load_events(path: Path = config.SECURITY_DB_PATH):
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError("pandas is required for dashboard metrics") from exc
    if not path.exists():
        return pd.DataFrame()
    with sqlite3.connect(path) as conn:
        return pd.read_sql_query("SELECT * FROM security_events ORDER BY timestamp DESC", conn)


def summarize_events(df):
    if df.empty:
        return {
            "total": 0,
            "allowed": 0,
            "flagged": 0,
            "blocked": 0,
            "redacted": 0,
            "output_escalations": 0,
        }
    return {
        "total": int(len(df)),
        "allowed": int((df["decision"] == "allow").sum()),
        "flagged": int((df["decision"] == "flag").sum()),
        "blocked": int((df["decision"] == "block").sum()),
        "redacted": int((df["decision"] == "redact").sum()),
        "output_escalations": int(df["output_risk_escalated"].astype(bool).sum()),
    }
