"""Runtime configuration for AIC-SAFE.

The PRD intentionally keeps tunable behavior in this file so reviewers can
audit model selection, risk thresholds, DLP patterns, and flagged-action policy
without changing middleware code.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
DATASET_DIR = BASE_DIR / "dataset"
MODEL_DIR = BASE_DIR / "models" / "saved"
EVALUATION_RESULTS_DIR = BASE_DIR / "evaluation" / "results"
RUN_LOG_PATH = EVALUATION_RESULTS_DIR / "run_log.jsonl"
RANDOM_SEED = 42

APP_DB_PATH = DATA_DIR / "app.db"
SECURITY_DB_PATH = DATA_DIR / "security_events.db"
JSONL_LOG_PATH = LOG_DIR / "security_events.jsonl"

MODEL_SELECTION = {
    "mode": "mock",  # mock for fast demos; use ollama for real local model output
    "ollama_model": "phi3:mini",
    "ollama_url": "http://localhost:11434",
    "request_timeout_seconds": 60,
    "warmup_timeout_seconds": 60,
    "num_predict": 128,
    "keep_alive": "10m",
    "warmup_prompt": "Reply with exactly: AIC-SAFE warmup ready.",
}

RISK_THRESHOLDS = {
    "flag_score": 0.35,
    "block_score": 0.70,
    "classifier_weight": 0.25,
}

FLAG_POLICY = {
    "db_read": {"proceed": True, "sanitized": True},
    "send_email": {"proceed": True, "sanitized": True},
    "export_data": {"proceed": False, "sanitized": True},
    "fake_api_cloud_action": {"proceed": True, "sanitized": True},
    "none": {"proceed": True, "sanitized": True},
}

DLP_PATTERNS = {
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "phone": r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b",
    "fake_api_key": r"\b(?:sk|pk|AKIA|AICSAFE)[-_]?[A-Za-z0-9]{12,}\b",
    "secret_assignment": r"(?i)\b(?:api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{8,}",
    "salary": r"(?i)\b(?:salary|compensation)\b[^.\n]{0,40}\$?\d{2,3}(?:,\d{3})+",
    "system_prompt": r"(?i)\b(?:system prompt|developer instructions|hidden instructions)\b",
}

ATTACK_CLASS_LABELS = {
    "direct_injection": "DIRECT_INJECTION",
    "indirect_rag_injection": "RAG_INJECTION_CLASSIFIER_ONLY",
    "multi_turn_accumulation": "MULTI_TURN_CLASSIFIER_ONLY",
    "agent_hijacking": "AGENT_HIJACKING",
    "prompt_leaking": "PROMPT_LEAKING",
    "payload_obfuscation": "PAYLOAD_OBFUSCATION",
    "jailbreak": "JAILBREAK",
    "benign": "BENIGN",
}

CLASSIFIER_PATHS = {
    "v1_week6": MODEL_DIR / "v1_week6" / "classifier.joblib",
    "v2_week12": MODEL_DIR / "v2_week12" / "classifier.joblib",
}

INTENT_CLASSIFIER_PATHS = {
    "v1_week6": MODEL_DIR / "v1_week6" / "intent_classifier.joblib",
    "v2_week12": MODEL_DIR / "v2_week12" / "intent_classifier.joblib",
}

DEFAULT_CLASSIFIER_VERSION = "v2_week12"

PROMPT_LOG_MAX_CHARS = 800
