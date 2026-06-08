from __future__ import annotations

import json
import shutil
import urllib.error
import urllib.request
import socket
import subprocess
import time
from dataclasses import dataclass

import config
from .mock_llm import MockLLM


class LLMGenerationError(RuntimeError):
    """Raised when the configured real LLM cannot return a response."""


class LLMTimeoutError(LLMGenerationError):
    """Raised when Ollama remains busy past the configured timeout."""


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

    def installed_models(self) -> list[str]:
        try:
            with urllib.request.urlopen(f"{self.base_url}/api/tags", timeout=5) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
            return []
        return [str(model.get("name", "")) for model in body.get("models", []) if model.get("name")]

    def model_is_installed(self) -> bool:
        return any(name == self.model or name.startswith(f"{self.model}:") for name in self.installed_models())

    def generate(self, prompt: str, timeout: int | None = None) -> str:
        options = {"temperature": 0, "seed": config.RANDOM_SEED}
        if config.MODEL_SELECTION.get("num_predict"):
            options["num_predict"] = int(config.MODEL_SELECTION["num_predict"])
        request_body = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": options,
        }
        if config.MODEL_SELECTION.get("keep_alive"):
            request_body["keep_alive"] = str(config.MODEL_SELECTION["keep_alive"])
        payload = json.dumps(request_body).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout or self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (TimeoutError, socket.timeout) as exc:
            active_timeout = timeout or self.timeout
            raise LLMTimeoutError(
                f"Ollama timed out after {active_timeout} seconds while generating with {self.model}. "
                "Keep Ollama running and try again; the first request can be slow while the model loads."
            ) from exc
        except urllib.error.URLError as exc:
            raise LLMGenerationError(
                f"Ollama is not reachable at {self.base_url}. Start Ollama with `ollama serve`."
            ) from exc
        except json.JSONDecodeError as exc:
            raise LLMGenerationError("Ollama returned an invalid JSON response.") from exc

        if "error" in body:
            raise LLMGenerationError(f"Ollama returned an error: {body['error']}")
        text = body.get("response", "").strip()
        if not text:
            raise LLMGenerationError("Ollama returned an empty response.")
        return text

    def warm_up(self) -> tuple[bool, str | None]:
        if self.mode != "ollama":
            return True, None
        if not self.is_available():
            return False, f"Ollama is not reachable at {self.base_url}."
        if not self.model_is_installed():
            return False, f"Ollama model `{self.model}` is not installed."
        try:
            self.generate(
                str(config.MODEL_SELECTION["warmup_prompt"]),
                timeout=int(config.MODEL_SELECTION["warmup_timeout_seconds"]),
            )
            return True, None
        except LLMGenerationError as exc:
            return False, str(exc)


def start_ollama_server(base_url: str | None = None, wait_seconds: float = 8.0) -> tuple[bool, str | None]:
    url = (base_url or config.MODEL_SELECTION["ollama_url"]).rstrip("/")
    probe = OllamaClient(
        base_url=url,
        model=str(config.MODEL_SELECTION["ollama_model"]),
        timeout=int(config.MODEL_SELECTION["request_timeout_seconds"]),
    )
    if probe.is_available():
        return True, "Ollama is already running."
    if not shutil.which("ollama"):
        return False, "Ollama command was not found on PATH."

    creationflags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            creationflags=creationflags,
        )
    except OSError as exc:
        return False, f"Could not start Ollama: {exc}"

    deadline = time.monotonic() + wait_seconds
    while time.monotonic() < deadline:
        if probe.is_available():
            return True, "Ollama started successfully."
        time.sleep(0.5)
    return False, f"Ollama was started, but {url} did not respond yet."


def build_llm_client(mode: str | None = None, start_ollama: bool = False) -> tuple[object, str | None]:
    selection = config.MODEL_SELECTION
    ollama = OllamaClient(
        base_url=selection["ollama_url"].rstrip("/"),
        model=selection["ollama_model"],
        timeout=int(selection["request_timeout_seconds"]),
    )
    requested = (mode or selection["mode"]).lower()
    if requested == "mock":
        return MockLLM(), "Mock LLM is explicitly configured. Runtime output is deterministic test/demo output."
    if requested != "ollama":
        raise ValueError("config.MODEL_SELECTION['mode'] must be 'ollama' or 'mock'.")
    startup_message = None
    if start_ollama:
        _, startup_message = start_ollama_server(ollama.base_url)
    if not ollama.is_available():
        return (
            ollama,
            startup_message
            or f"Ollama is not reachable at {ollama.base_url}. Start Ollama with `ollama serve` before running prompts.",
        )
    if not ollama.model_is_installed():
        return (
            ollama,
            f"Ollama is running, but model `{ollama.model}` is not installed. Run `ollama pull {ollama.model}`.",
        )
    return ollama, None
