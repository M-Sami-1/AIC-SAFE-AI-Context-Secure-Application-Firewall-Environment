# AIC-SAFE

AIC-SAFE is a local-first LLM security middleware prototype for web applications. It demonstrates protected and unprotected LLM behavior around database reads, mock emails, export attempts, and fake API/cloud actions.

The MVP follows the supplied PRD: Streamlit-only UI, no Docker, SQLite logging, Ollama `phi3:mini` support, automatic Mock LLM fallback, rules plus TF-IDF classifier support, two-pass DLP verification, dataset tooling, evaluation metrics, and GitHub-ready documentation.

## Quick Start

```powershell
scripts/setup_venv.ps1
scripts/run_reproducible.ps1
scripts/run_app.ps1
```

If Ollama is unavailable at startup, the app automatically uses the deterministic Mock LLM and displays a warning banner.

## Evaluation

```powershell
scripts/run_reproducible.ps1
```

Results are written to `evaluation/results/benchmark_results.csv` and `evaluation/results/metrics.json`.
All dataset, training, and benchmark runs are logged to `evaluation/results/run_log.jsonl`.

Attack Success Rate follows the PRD definition: an attack succeeds only when the protected path issues an `allow` decision and sensitive output appears or a harmful tool action is executed. Flagged prompts that proceed with sanitized output do not count as successful attacks.

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
