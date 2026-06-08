from __future__ import annotations

import re
from pathlib import Path

import config
from aic_safe.types import ScanResult


ATTACK_PATTERNS: dict[str, list[str]] = {
    "direct_injection": [
        r"(?i)\bignore (?:all )?(?:previous|above|prior) instructions\b",
        r"(?i)\boverride\b.*\binstructions\b",
        r"(?i)\bdisregard\b.*\bpolicy\b",
    ],
    "indirect_rag_injection": [
        r"(?i)\bwhen this document is retrieved\b",
        r"(?i)\brag\b.*\binjection\b",
        r"(?i)\bhidden instruction in (?:the )?document\b",
    ],
    "multi_turn_accumulation": [
        r"(?i)\bremember this for later\b",
        r"(?i)\bin the next message\b.*\bignore\b",
        r"(?i)\bgradually\b.*\bchange\b.*\binstructions\b",
    ],
    "agent_hijacking": [
        r"(?i)\bcall the tool\b",
        r"(?i)\buse your tools?\b.*\bwithout\b.*\bpermission\b",
        r"(?i)\bexecute\b.*\b(?:webhook|cloud|database|export)\b",
    ],
    "prompt_leaking": [
        r"(?i)\breveal\b.*\b(?:system|developer|hidden) instructions\b",
        r"(?i)\bshow\b.*\bsystem prompt\b",
        r"(?i)\bprint\b.*\bpolicy\b",
    ],
    "payload_obfuscation": [
        r"(?i)\bbase64\b",
        r"(?i)\brot13\b",
        r"(?i)\bdecode\b.*\bthen\b.*\bexecute\b",
        r"(?i)\bunicode\b.*\bescape\b",
    ],
    "jailbreak": [
        r"(?i)\bdeveloper mode\b",
        r"(?i)\bdo anything now\b",
        r"(?i)\bno restrictions\b",
        r"(?i)\bpretend\b.*\bunfiltered\b",
    ],
}

SUSPICIOUS_PATTERNS = [
    r"(?i)\bsecret\b",
    r"(?i)\bapi[_ -]?key\b",
    r"(?i)\btoken\b",
    r"(?i)\bsalary\b",
    r"(?i)\ball customers\b",
    r"(?i)\bexport\b.*\b(?:all|full|complete)\b",
]


class PromptSafetyScanner:
    def __init__(self, classifier_version: str | None = None, use_classifier: bool = True) -> None:
        self.classifier_version = classifier_version or config.DEFAULT_CLASSIFIER_VERSION
        self._classifier = (
            self._load_classifier(config.CLASSIFIER_PATHS.get(self.classifier_version))
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

    def scan(self, prompt: str) -> ScanResult:
        matches: list[str] = []
        class_scores: dict[str, int] = {}
        for attack_class, patterns in ATTACK_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, prompt):
                    matches.append(pattern)
                    class_scores[attack_class] = class_scores.get(attack_class, 0) + 1

        suspicious_count = 0
        for pattern in SUSPICIOUS_PATTERNS:
            if re.search(pattern, prompt):
                matches.append(pattern)
                suspicious_count += 1

        attack_class = max(class_scores, key=class_scores.get) if class_scores else "benign"
        score = min(1.0, (sum(class_scores.values()) * 0.60) + (suspicious_count * 0.16))
        classifier_available = self._classifier is not None
        confidence = 0.60 if matches else 0.78

        if classifier_available:
            try:
                probabilities = self._classifier.predict_proba([prompt])[0]
                classes = list(self._classifier.classes_)
                predicted = str(self._classifier.predict([prompt])[0])
                attack_probability = 1.0 - probabilities[classes.index("benign")] if "benign" in classes else max(probabilities)
                score = min(1.0, score + (attack_probability * config.RISK_THRESHOLDS["classifier_weight"]))
                confidence = max(confidence, float(max(probabilities)))
                if attack_class == "benign" and predicted != "benign":
                    attack_class = predicted
            except Exception:
                classifier_available = False

        if score >= config.RISK_THRESHOLDS["block_score"]:
            label = "attack"
        elif score >= config.RISK_THRESHOLDS["flag_score"]:
            label = "suspicious"
        else:
            label = "benign"

        reason = "No prompt-injection indicators matched."
        if matches:
            reason = f"Matched {len(matches)} prompt safety indicator(s); strongest class: {attack_class}."

        return ScanResult(
            label=label,
            risk_score=round(score, 3),
            confidence=round(confidence, 3),
            matched_patterns=matches,
            attack_class=attack_class,
            reason=reason,
            classifier_available=classifier_available,
        )
