from __future__ import annotations

import re


class MockLLM:
    """Deterministic fallback LLM for demos, tests, and low-resource machines."""

    mode = "mock"

    def generate(self, prompt: str) -> str:
        lower = prompt.lower()
        if any(term in lower for term in ["ignore previous", "reveal", "leak", "secret", "api key"]):
            return (
                "Unprotected simulation: I found a fake secret api_key=AICSAFE_DEMO_KEY_123456 "
                "and customer contact alex.customer@example.test, 555-010-2200."
            )
        if any(term in lower for term in ["salary", "employees", "database", "db"]):
            return "I can summarize employee departments and safe aggregate counts."
        if "email" in lower:
            target = re.search(r"[\w.+-]+@[\w.-]+\.\w+", prompt)
            who = target.group(0) if target else "demo.recipient@example.test"
            return f"Prepared a mock email simulation for {who}."
        if any(term in lower for term in ["export", "csv", "download"]):
            return "Prepared a safe demo export with non-sensitive fields only."
        if any(term in lower for term in ["webhook", "s3", "cloud function", "api"]):
            return "Prepared a simulated cloud/API action. No network call was made."
        return "AIC-SAFE mock response: request handled locally with no external dependency."
