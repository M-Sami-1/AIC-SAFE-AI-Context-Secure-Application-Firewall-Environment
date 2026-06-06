from __future__ import annotations

import re

import config


class DLPScanner:
    def __init__(self, patterns: dict[str, str] | None = None) -> None:
        self.patterns = patterns or config.DLP_PATTERNS

    def scan(self, text: str) -> dict[str, list[str]]:
        matches: dict[str, list[str]] = {}
        for name, pattern in self.patterns.items():
            found = re.findall(pattern, text)
            if found:
                matches[name] = [item if isinstance(item, str) else " ".join(item) for item in found]
        return matches

    def risk_for_matches(self, matches: dict[str, list[str]]) -> str:
        if not matches:
            return "low"
        high_risk = {"fake_api_key", "secret_assignment", "salary", "system_prompt"}
        return "high" if any(key in high_risk for key in matches) else "medium"

    def redact(self, text: str, matches: dict[str, list[str]] | None = None) -> str:
        redacted = text
        active = matches or self.scan(text)
        for name in active:
            redacted = re.sub(self.patterns[name], f"[REDACTED:{name}]", redacted)
        return redacted
