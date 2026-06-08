# AIC-SAFE Running and Testing Guide

This guide explains how to set up, run, and verify the AIC-SAFE MVP locally.

## 1. Prerequisites

- Windows PowerShell
- Python 3.11. The project can use a local interpreter at `.python311\python.exe`.
- Internet access for the first dependency install
- Optional for realistic app prompts: Ollama installed with `phi3:mini`

Docker is not required.

## 2. Fastest Way to Run the App

From the project root:

```powershell
cd "C:\Users\S S C\Desktop\AI_Proto"
.\start.ps1
```

This creates or refreshes `.venv`, installs dependencies, prepares missing dataset/model artifacts, starts Ollama if it is installed, warms `phi3:mini` if available, and opens the Streamlit app.

The app usually opens at:

```text
http://localhost:8501
```

Use the sidebar runtime toggle:

```text
Use Ollama off: fast local mock mode
Use Ollama on: real local Ollama mode
```

Fast local mock mode is the default and should return results in a few seconds or less. Ollama mode uses real local generation and depends on your hardware.

## 3. Create Only the Project Virtual Environment

If you do not want to use `start.ps1`, set up the environment manually:

```powershell
cd "C:\Users\S S C\Desktop\AI_Proto"
scripts/setup_venv.ps1
```

This creates `.venv`, installs pinned dependencies from `requirements.txt`, and writes `requirements.lock.txt`.

## 4. Run Dataset Generation, Training, Evaluation, and Tests

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

## 5. Run the Streamlit App Manually

After `.venv` exists, run:

```powershell
.\.venv\Scripts\python.exe app.py
```

Streamlit will print a local URL, usually:

```text
http://localhost:8501
```

Open that URL in your browser. The app starts in fast local mock mode unless `config.py` is changed. Turn on `Use Ollama` in the sidebar for real local model output.

The app attempts to start and warm Ollama automatically. To prepare Ollama yourself, run:

```powershell
ollama pull phi3:mini
ollama serve
```

Then refresh the app and enable `Use Ollama`.

`scripts/run_app.ps1` still works too, but `python app.py` is the simplest single-file launcher.

## 6. Verify the App Is Working

Before running checks, confirm the sidebar shows:

```text
LLM mode: mock
```

For realistic local generation, turn on `Use Ollama` and wait for the warm-up message. The sidebar should then show:

```text
LLM mode: ollama
```

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
   - LLM mode should match the sidebar toggle: `mock` or `ollama`.

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

## 7. Verify Logs

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

## 8. Run Only Tests

After `.venv` is created:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Expected result:

```text
all tests pass
```

## 9. Run Only the App

```powershell
.\.venv\Scripts\python.exe app.py
```

## 10. Run Only the Benchmark

The benchmark entry point enforces the project `.venv`. Use:

```powershell
.\.venv\Scripts\python.exe -m evaluation.benchmark
```

For a faster smoke test:

```powershell
.\.venv\Scripts\python.exe -m evaluation.benchmark --limit 3 --runtime-mode mock
```

For realistic Ollama benchmark output:

```powershell
.\.venv\Scripts\python.exe -m evaluation.benchmark --limit 3 --runtime-mode ollama
```

Use small limits with Ollama because each sample runs raw, rule-only, and full middleware paths.

## 11. Ollama Setup

For realistic local model results, install Ollama and pull the model:

```powershell
ollama pull phi3:mini
ollama serve
```

Then run:

```powershell
.\.venv\Scripts\python.exe app.py
```

Turn on `Use Ollama` in the app sidebar.

To run deterministic fast demo/test output, leave `Use Ollama` off or keep `config.py` in mock mode:

```python
MODEL_SELECTION = {
    "mode": "mock",
    ...
}
```

Switch it to `"ollama"` only if you want the app to open with Ollama enabled by default.

### Ollama timeout

The first request can be slow while the model loads. The app starts and warms Ollama in the background, but hardware still controls generation speed. The app timeout is configured in `config.py` as:

```python
"request_timeout_seconds": 60
```

If you still see a timeout, confirm Ollama is serving and the model is installed:

```powershell
ollama list
ollama run phi3:mini "answer in one sentence"
```

## 12. Troubleshooting

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

### App is still slow

Check the sidebar:

```text
Use Ollama off
```

Fast local mock mode should be quick. If `Use Ollama` is on, the app is waiting on real local model generation. Ollama speed depends on model size, CPU/GPU, available RAM, and whether the model is already warm.

## 13. Recommended Reviewer Flow

For a complete review, run these commands in order:

```powershell
cd "C:\Users\S S C\Desktop\AI_Proto"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\start.ps1 -FullSetup
```

Then verify:

```text
Protected Mode blocks or sanitizes attacks.
Unprotected Mode shows baseline unsafe behavior.
LLM mode shows mock by default for fast demos.
Use Ollama toggle switches to real local model output when Ollama is available.
Dashboard shows logged events.
evaluation/results/metrics.json exists.
evaluation/results/run_log.jsonl exists.
pytest passes.
```
