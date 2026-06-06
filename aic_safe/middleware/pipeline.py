from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone

from aic_safe.llm import build_llm_client
from aic_safe.types import PipelineResult, RiskDecision, VerificationResult

from .gateway import ToolGateway, execute_unprotected_action
from .input_scanner import PromptSafetyScanner
from .intent_classifier import ToolIntentClassifier
from .logger import SecurityLogger, truncate_prompt
from .output_verifier import OutputVerifier
from .risk_engine import RiskDecisionEngine


class AICSafePipeline:
    def __init__(self, llm_client: object | None = None, logger: SecurityLogger | None = None) -> None:
        self.llm_client, self.startup_warning = (llm_client, None) if llm_client else build_llm_client()
        self.logger = logger or SecurityLogger()
        self.scanner = PromptSafetyScanner()
        self.intent_classifier = ToolIntentClassifier()
        self.risk_engine = RiskDecisionEngine()
        self.gateway = ToolGateway()
        self.output_verifier = OutputVerifier()

    @property
    def llm_mode(self) -> str:
        return getattr(self.llm_client, "mode", "unknown")

    def run_protected(self, prompt: str, attack_class: str | None = None) -> PipelineResult:
        started = time.perf_counter()
        prompt_id = str(uuid.uuid4())
        scan = self.scanner.scan(prompt)
        if attack_class:
            scan = scan.__class__(**{**scan.__dict__, "attack_class": attack_class})
        intent = self.intent_classifier.classify(prompt)
        risk = self.risk_engine.decide(scan, intent)
        tool_result = self.gateway.execute(prompt, intent, risk)

        if risk.decision == "block":
            raw_response = f"AIC-SAFE blocked this request. {risk.reason}"
        else:
            raw_response = self.llm_client.generate(self._build_prompt(prompt, risk))
            if tool_result:
                raw_response = f"{raw_response}\n\nTool result: {json.dumps(tool_result.data, default=str)}"

        verification = self.output_verifier.verify(raw_response, risk.risk_level)
        latency_ms = int((time.perf_counter() - started) * 1000)
        event = self._event(
            prompt_id=prompt_id,
            mode="protected",
            source_label="PROTECTED",
            prompt=prompt,
            prompt_safety_label=scan.label,
            attack_class=scan.attack_class,
            tool_intent=intent.tool_intent,
            risk_level=verification.risk_level,
            decision=risk.decision if verification.decision == "allow" else verification.decision,
            reason=f"{risk.reason} {verification.reason}",
            llm_mode=self.llm_mode,
            latency_ms=latency_ms,
            config_flag_key=risk.config_flag_key,
            output_risk_escalated=verification.output_risk_escalated,
        )
        self.logger.write(event)
        return PipelineResult(
            prompt_id,
            "protected",
            "PROTECTED",
            prompt,
            scan,
            intent,
            risk,
            self.llm_mode,
            raw_response,
            tool_result,
            verification,
            latency_ms,
            event,
        )

    @staticmethod
    def _build_prompt(prompt: str, risk: RiskDecision) -> str:
        if risk.decision == "flag":
            return (
                "AIC-SAFE note: answer safely and do not reveal secrets, credentials, salaries, "
                f"or private contacts. User prompt: {prompt}"
            )
        return prompt

    @staticmethod
    def _event(**kwargs) -> dict:
        return {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prompt_text": truncate_prompt(kwargs.pop("prompt")),
            **kwargs,
        }


def run_unprotected(prompt: str, llm_client: object | None = None, logger: SecurityLogger | None = None, attack_class: str | None = None) -> PipelineResult:
    started = time.perf_counter()
    prompt_id = str(uuid.uuid4())
    client, _ = (llm_client, None) if llm_client else build_llm_client()
    event_logger = logger or SecurityLogger()
    scanner = PromptSafetyScanner()
    intent_classifier = ToolIntentClassifier()
    verifier = OutputVerifier()
    scan = scanner.scan(prompt)
    if attack_class:
        scan = scan.__class__(**{**scan.__dict__, "attack_class": attack_class})
    intent = intent_classifier.classify(prompt)
    tool_result = execute_unprotected_action(prompt, intent)
    raw_response = client.generate(prompt)
    if tool_result:
        raw_response = f"{raw_response}\n\nTool result: {json.dumps(tool_result.data, default=str)}"
    output_matches = verifier.dlp.scan(raw_response)
    verification = VerificationResult(
        final_text=raw_response,
        risk_level=verifier.dlp.risk_for_matches(output_matches),
        decision="allow",
        matches=output_matches,
        sensitive_output=bool(output_matches),
        reason="Unprotected baseline did not apply AIC-SAFE output controls.",
    )
    latency_ms = int((time.perf_counter() - started) * 1000)
    risk = RiskDecision("low", "allow", "Unprotected baseline bypassed AIC-SAFE middleware.")
    event = AICSafePipeline._event(
        prompt_id=prompt_id,
        mode="unprotected",
        source_label="UNPROTECTED",
        prompt=prompt,
        prompt_safety_label=scan.label,
        attack_class=scan.attack_class,
        tool_intent=intent.tool_intent,
        risk_level=verification.risk_level,
        decision="allow",
        reason="Unprotected baseline executed without middleware controls.",
        llm_mode=getattr(client, "mode", "unknown"),
        latency_ms=latency_ms,
        config_flag_key=None,
        output_risk_escalated=verification.output_risk_escalated,
    )
    event_logger.write(event)
    return PipelineResult(
        prompt_id,
        "unprotected",
        "UNPROTECTED",
        prompt,
        scan,
        intent,
        risk,
        getattr(client, "mode", "unknown"),
        raw_response,
        tool_result,
        verification,
        latency_ms,
        event,
    )
