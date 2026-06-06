# Configuration Reference

All MVP tuning lives in `config.py`.

- `MODEL_SELECTION`: controls `auto`, `ollama`, or `mock` mode, Ollama URL, model name, and timeout.
- `RISK_THRESHOLDS`: controls medium-risk flag and high-risk block score cutoffs.
- `FLAG_POLICY`: maps action types to flagged prompt behavior.
- `DLP_PATTERNS`: regular expressions for fake API keys, emails, phone numbers, salary data, secret assignments, and system prompt leakage.
- `ATTACK_CLASS_LABELS`: display labels used by evaluation reports.
- `CLASSIFIER_PATHS`: versioned TF-IDF checkpoints for `v1_week6` and `v2_week12`.
- `INTENT_CLASSIFIER_PATHS`: versioned TF-IDF checkpoints for tool-intent classification.
- `RANDOM_SEED`: deterministic seed for train/test splitting and classifier training.
- `RUN_LOG_PATH`: JSONL manifest for reproducible dataset, training, and benchmark runs.

Default flag behavior:

| Action | Flagged Behavior |
| --- | --- |
| `db_read` | Proceed with sanitized/limited result |
| `send_email` | Proceed with safe simulation |
| `export_data` | Hold action |
| `fake_api_cloud_action` | Proceed with safe simulation |
| `none` | Proceed safely |
