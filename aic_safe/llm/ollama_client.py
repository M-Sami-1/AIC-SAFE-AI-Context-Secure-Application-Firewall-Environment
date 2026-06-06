from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

import config
from .mock_llm import MockLLM


@dataclass
class OllamaClient:
    base_url: str
    model: str
    timeout: int

    mode: str = "ollama"

    def is_available(self) -> bool:
        try:
            with urllib.request.urlopen(f"{self.base_url}/api/tags", timeout=2) as response:
                return response.status == 200
        except (urllib.error.URLError, TimeoutError, OSError):
            return False

    def generate(self, prompt: str) -> str:
        payload = json.dumps({"model": self.model, "prompt": prompt, "stream": False}).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
        return body.get("response", "").strip()


def build_llm_client() -> tuple[object, str | None]:
    selection = config.MODEL_SELECTION
    ollama = OllamaClient(
        base_url=selection["ollama_url"].rstrip("/"),
        model=selection["ollama_model"],
        timeout=int(selection["request_timeout_seconds"]),
    )
    requested = selection["mode"].lower()
    if requested == "mock":
        return MockLLM(), None
    if requested == "ollama":
        if not ollama.is_available():
            return MockLLM(), "Ollama was requested but is unavailable; using Mock LLM fallback."
        return ollama, None
    if ollama.is_available():
        return ollama, None
    return MockLLM(), "Ollama is unavailable at startup; AIC-SAFE auto-switched to Mock LLM fallback."
