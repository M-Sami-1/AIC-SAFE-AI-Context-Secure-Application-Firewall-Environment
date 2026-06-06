# Setup

## Requirements

- Python 3.11 recommended
- 6-8 GB RAM
- No Docker required
- Optional: Ollama with `phi3:mini`

## Install

```powershell
scripts/setup_venv.ps1
scripts/run_reproducible.ps1
scripts/run_app.ps1
```

When Ollama is not reachable, `config.MODEL_SELECTION["mode"] = "auto"` switches to Mock LLM automatically and the app shows a warning banner.

Dataset generation, classifier training, evaluation, and tests are intended to run only through the project `.venv`. See `docs/reproducibility.md`.
