from __future__ import annotations

import re
from pathlib import Path

import config
from aic_safe.types import IntentResult


INTENT_PATTERNS: dict[str, list[str]] = {
    "db_read": [
        r"(?i)\b(?:database|db|sqlite|table|records?)\b",
        r"(?i)\b(?:employees?|customers?|salaries|secrets)\b",
        r"(?i)\bquery\b.*\b(?:employees|customers|secrets)\b",
    ],
    "send_email": [
        r"(?i)\b(?:send|draft|email|mail)\b",
        r"(?i)[\w.+-]+@[\w.-]+\.\w+",
    ],
    "export_data": [
        r"(?i)\b(?:export|download|dump|csv|spreadsheet)\b",
        r"(?i)\b(?:all|full|complete)\b.*\b(?:data|records|table)\b",
    ],
    "fake_api_cloud_action": [
        r"(?i)\b(?:s3|webhook|cloud function|api call|trigger|upload)\b",
        r"(?i)\b(?:mock cloud|fake cloud|lambda)\b",
    ],
}


class ToolIntentClassifier:
    def __init__(self, classifier_version: str | None = None, use_classifier: bool = True) -> None:
        self.classifier_version = classifier_version or config.DEFAULT_CLASSIFIER_VERSION
        self._classifier = (
            self._load_classifier(config.INTENT_CLASSIFIER_PATHS.get(self.classifier_version))
            if use_classifier
            else None
        )

    @staticmethod
    def _load_classifier(path: Path | None):
        if not path or not path.exists():
            return None
        try:
            import joblib

            return joblib.load(path)
        except Exception:
            return None

    def classify(self, prompt: str) -> IntentResult:
        best_intent = "none"
        best_matches: list[str] = []
        for intent, patterns in INTENT_PATTERNS.items():
            matches = [pattern for pattern in patterns if re.search(pattern, prompt)]
            if len(matches) > len(best_matches):
                best_intent = intent
                best_matches = matches

        classifier_intent = None
        classifier_confidence = 0.0
        if self._classifier is not None:
            try:
                classifier_intent = str(self._classifier.predict([prompt])[0])
                probabilities = self._classifier.predict_proba([prompt])[0]
                classifier_confidence = float(max(probabilities))
            except Exception:
                classifier_intent = None

        if classifier_intent and (best_intent == "none" or classifier_confidence >= 0.72):
            return IntentResult(
                classifier_intent,
                round(classifier_confidence, 3),
                best_matches,
                f"TF-IDF intent classifier detected protected action intent: {classifier_intent}.",
            )

        if best_intent == "none":
            return IntentResult("none", 0.95, [], "No protected tool intent detected.")

        confidence = min(0.95, 0.45 + (0.2 * len(best_matches)))
        return IntentResult(
            best_intent,
            round(confidence, 3),
            best_matches,
            f"Detected protected action intent: {best_intent}.",
        )
