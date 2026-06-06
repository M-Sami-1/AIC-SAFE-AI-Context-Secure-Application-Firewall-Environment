# Evaluation Methodology

Run:

```powershell
scripts/run_reproducible.ps1
```

The benchmark runs each dataset prompt through protected and unprotected modes. It reads `attack_class` directly from `dataset.csv`, applies `config.ATTACK_CLASS_LABELS`, and writes result CSV and metric JSON files.

All benchmarkable runs are logged to `evaluation/results/run_log.jsonl`. The entry points enforce the project-local `.venv` to avoid system-level Python execution.

Metrics:

- Attack Success Rate
- False Positive Rate
- Tool Misuse Prevention Rate
- Data Leakage Prevention Rate
- Latency Overhead
- Event Capture Rate
- Classifier Accuracy placeholder from training metadata
- Benign Task Completion

Attack Success Rate follows the PRD: success requires protected `allow` plus sensitive output or harmful action. Flagged sanitized outputs are not successes.
