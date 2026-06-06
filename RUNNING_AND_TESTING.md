# AIC-SAFE Running and Testing Guide

This guide explains how to set up, run, and verify the AIC-SAFE MVP locally.

## 1. Prerequisites

- Windows PowerShell
- Python 3.11. The project can use a local interpreter at `.python311\python.exe`.
- Internet access for the first dependency install
- Optional: Ollama installed with `phi3:mini`

Docker is not required.

## 2. Create the Project Virtual Environment

From the project root:

```powershell
cd "C:\Users\S S C\Desktop\AI_Proto"
scripts/setup_venv.ps1
```

This creates `.venv`, installs pinned dependencies from `requirements.txt`, and writes `requirements.lock.txt`.

## 3. Run Dataset Generation, Training, Evaluation, and Tests

Use the controlled reproducible workflow:

```powershell
scripts/run_reproducible.ps1
```

This runs:

```text
dataset generation
TF-IDF prompt safety training: v1_week6
TF-IDF prompt safety training: v2_week12
TF-IDF tool intent training
evaluation benchmark
pytest test suite
```

Expected generated outputs:

```text
dataset/raw_attacks.csv
dataset/raw_benign.csv
dataset/dataset.csv
models/saved/v1_week6/classifier.joblib
models/saved/v1_week6/intent_classifier.joblib
models/saved/v1_week6/metadata.json
models/saved/v2_week12/classifier.joblib
models/saved/v2_week12/intent_classifier.joblib
models/saved/v2_week12/metadata.json
evaluation/results/benchmark_results.csv
evaluation/results/metrics.json
evaluation/results/run_log.jsonl
logs/reproducible_run_*.log
```

## 4. Run the Streamlit App

After setup:

```powershell
scripts/run_app.ps1
```

Streamlit will print a local URL, usually:

```text
http://localhost:8501
```

Open that URL in your browser.

## 5. Verify the App Is Working

### Protected Mode Check

1. Open the `Protected Mode` tab.
2. Select `Direct injection`.
3. Click `Run Protected`.
4. Expected result:
   - Risk should be `HIGH`.
   - Decision should be `BLOCK` or protected by DLP.
   - Source label in the event summary should be `PROTECTED`.

### Unprotected Mode Check

1. Open the `Unprotected Mode` tab.
2. Use the same direct injection prompt.
3. Click `Run Unprotected`.
4. Expected result:
   - The app should show baseline behavior without middleware blocking.
   - Source label should be `UNPROTECTED`.

### Comparison Check

1. Open the `Compare` tab.
2. Use the default prompt.
3. Click `Run Both Modes`.
4. Expected result:
   - Protected output should block, sanitize, redact, or limit the risky request.
   - Unprotected output should demonstrate the unsafe baseline.

### Dashboard Check

1. Open the `Security Dashboard` tab.
2. Confirm metrics are visible.
3. Confirm recent events appear in the table.
4. Test filters for:
   - `PROTECTED`
   - `UNPROTECTED`
   - risk levels

## 6. Verify Logs

Security events are written to:

```text
logs/security_events.jsonl
data/security_events.db
```

Reproducible run metadata is written to:

```text
evaluation/results/run_log.jsonl
```

Each benchmarkable run records:

```text
timestamp
run type
status
Python executable
whether the project .venv was used
random seed
requirements.txt hash
output paths
run-specific metrics
```

## 7. Run Only Tests

After `.venv` is created:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Expected result:

```text
all tests pass
```

## 8. Run Only the App

```powershell
scripts/run_app.ps1
```

## 9. Run Only the Benchmark

The benchmark entry point enforces the project `.venv`. Use:

```powershell
.\.venv\Scripts\python.exe -m evaluation.benchmark
```

For a faster smoke test:

```powershell
.\.venv\Scripts\python.exe -m evaluation.benchmark --limit 20
```

## 10. Optional Ollama Setup

If Ollama is installed:

```powershell
ollama pull phi3:mini
ollama serve
```

Then run:

```powershell
scripts/run_app.ps1
```

If Ollama is unavailable, AIC-SAFE automatically switches to the Mock LLM fallback and displays a warning banner in the app.

## 11. Troubleshooting

### PowerShell blocks scripts

Run PowerShell as your user and allow local scripts for the current session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then rerun:

```powershell
scripts/setup_venv.ps1
```

### Python is not found

Install Python 3.11 or use the project-local `.python311\python.exe` interpreter.

Check:

```powershell
.\.python311\python.exe --version
```

### Missing `.venv`

Run:

```powershell
scripts/setup_venv.ps1
```

### Benchmark refuses to run

Dataset generation, training, and benchmark scripts are designed to run only inside the project `.venv`.

Use:

```powershell
scripts/run_reproducible.ps1
```

## 12. Recommended Reviewer Flow

For a complete review, run these commands in order:

```powershell
cd "C:\Users\S S C\Desktop\AI_Proto"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
scripts/setup_venv.ps1
scripts/run_reproducible.ps1
scripts/run_app.ps1
```

Then verify:

```text
Protected Mode blocks or sanitizes attacks.
Unprotected Mode shows baseline unsafe behavior.
Dashboard shows logged events.
evaluation/results/metrics.json exists.
evaluation/results/run_log.jsonl exists.
pytest passes.
```
