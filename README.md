# AIC-SAFE

AIC-SAFE is a local-first LLM security middleware prototype for web applications. It demonstrates protected and unprotected LLM behavior around database reads, simulated emails, export attempts, and simulated API/cloud actions.

The MVP follows the supplied PRD: Streamlit-only UI, no Docker, SQLite logging, optional real Ollama `phi3:mini` generation, fast deterministic local demo mode, rules plus TF-IDF classifier support, two-pass DLP verification, dataset tooling, evaluation metrics, and GitHub-ready documentation.

## Quick Start

```powershell
.\start.ps1
```

The startup script creates or refreshes `.venv`, installs dependencies, prepares missing dataset/model artifacts, starts Ollama when available, ensures `phi3:mini` is present, and launches the Streamlit app. Use `.\start.ps1 -FullSetup` to also run the benchmark and tests.

The app starts in fast local mock mode by default so `Run Protected` and `Run Unprotected` return quickly. In the sidebar, turn on `Use Ollama` when you want real local model output from `phi3:mini`. The app also tries to start and warm Ollama in the background when available.

## Runtime Realism

- Fast local mock mode is the default for quick demos and repeatable testing.
- Ollama mode is available from the sidebar toggle for realistic local model generation.
- Application data is local SQLite demo data seeded in `data/app.db`.
- Email, export, and API/cloud actions are simulated on purpose; they do not send real emails, call cloud APIs, or move real customer data.
- Automated tests inject deterministic test clients so tests stay repeatable without depending on a live Ollama process.

## Evaluation

```powershell
scripts/run_reproducible.ps1
```

Results are written to `evaluation/results/benchmark_results.csv` and `evaluation/results/metrics.json`.
All dataset, training, and benchmark runs are logged to `evaluation/results/run_log.jsonl`.

The benchmark compares three modes: `raw_llm`, `rule_only`, and `full_middleware`. Metrics include Attack Success Rate, False Positive Rate, True Positive Detection Rate, Tool Misuse Success Rate, and average latency overhead.

Attack Success Rate follows the PRD definition: an attack succeeds only when a mode issues an `allow` decision and sensitive output appears or a harmful simulated tool action occurs. Blocked or sanitized outputs do not count as successful attacks.

## Project Structure

The implementation mirrors the PRD repository layout:

- `app.py`: Streamlit application with Protected, Unprotected, Compare, Dashboard, and Evaluation sections.
- `config.py`: model selection, risk thresholds, DLP patterns, flag policy, and attack label mapping.
- `aic_safe/middleware`: scanner, intent classifier, risk engine, gateway, DLP, output verifier, logger, and pipeline.
- `aic_safe/tools`: SQLite database, mock email, export, and fake API/cloud simulators.
- `dataset`: raw and combined dataset builder.
- `models`: TF-IDF training script and versioned checkpoint directories.
- `evaluation`: benchmark runner and metrics.
- `docs`: setup, architecture, configuration, dataset policy, evaluation, and Phase 2 RAG notes.

## Scope Notes

RAG runtime protection, real IAM, real cloud APIs, Docker services, Wazuh, Elastic, Kibana, and BERT training are intentionally excluded from the MVP. `indirect_rag_injection` and `multi_turn_accumulation` samples are included for classifier training and evaluation labeling only.
