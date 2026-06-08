# Architecture

AIC-SAFE is a Streamlit application wrapped around a modular middleware pipeline.

1. The selected UI tab assigns `source_label` as `PROTECTED` or `UNPROTECTED`.
2. Protected prompts pass through the prompt scanner and tool intent classifier.
3. The risk engine converts scanner output into `allow`, `flag`, or `block`.
4. Every database, email, export, or fake API/cloud action passes through the gateway.
5. The LLM client uses the configured runtime. The default is real Ollama generation; Mock LLM is available only when explicitly configured or injected by tests.
6. The output verifier performs two-pass DLP: inherit input risk, then escalate if output patterns are detected.
7. Security events are written to JSONL and SQLite with source label, config flag key, risk, decision, and latency.
8. The dashboard and benchmark read the same event schema for review and research evidence.

The LLM never receives direct authority to execute environment-facing actions in protected mode.
