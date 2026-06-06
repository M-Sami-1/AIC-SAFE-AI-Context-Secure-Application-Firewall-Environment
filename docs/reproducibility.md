# Reproducibility Policy

AIC-SAFE benchmarkable runs must execute inside the project-local virtual environment at `.venv`.
The `.venv` can be created from a project-local Python interpreter at `.python311\python.exe`, keeping Python execution scoped to this repository.

Supported flow:

```powershell
scripts/setup_venv.ps1
scripts/run_reproducible.ps1
```

The project does not require Docker because the PRD excludes containers. The fixed `.venv` is the controlled sandbox for dataset generation, classifier training, evaluation, and tests.

Guardrails:

- `requirements.txt` uses exact pinned versions.
- `scripts/setup_venv.ps1` creates `.venv` and writes `requirements.lock.txt` from `pip freeze`.
- Dataset generation, training, and benchmark entry points refuse to run outside `.venv`.
- `config.RANDOM_SEED` controls deterministic training and splitting.
- `evaluation/results/run_log.jsonl` records each dataset, training, and benchmark run.
- `logs/reproducible_run_*.log` records the full PowerShell transcript for the controlled workflow.

Run log fields include:

- timestamp
- run type
- status
- Python executable
- whether execution occurred inside `.venv`
- random seed
- `requirements.txt` SHA-256
- run-specific metadata and output paths
