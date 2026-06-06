from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import config


def project_venv_python() -> Path:
    if sys.platform.startswith("win"):
        return config.BASE_DIR / ".venv" / "Scripts" / "python.exe"
    return config.BASE_DIR / ".venv" / "bin" / "python"


def inside_project_venv() -> bool:
    expected = project_venv_python().resolve()
    current = Path(sys.executable).resolve()
    return current == expected


def enforce_project_venv() -> None:
    """Refuse benchmarkable runs outside the project-local virtualenv."""

    if not inside_project_venv():
        raise RuntimeError(
            "AIC-SAFE reproducible runs must use the project-local virtual environment. "
            "Run scripts/setup_venv.ps1 once, then use scripts/run_reproducible.ps1."
        )


def file_sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def log_run(run_type: str, status: str, metadata: dict[str, Any] | None = None) -> None:
    config.EVALUATION_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_type": run_type,
        "status": status,
        "python_executable": str(Path(sys.executable).resolve()),
        "inside_project_venv": inside_project_venv(),
        "random_seed": config.RANDOM_SEED,
        "requirements_sha256": file_sha256(config.BASE_DIR / "requirements.txt"),
        "metadata": metadata or {},
    }
    with config.RUN_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
