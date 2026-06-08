from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone

from aic_safe.llm import LLMGenerationError, build_llm_client
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
        return self.run_full_middleware(prompt, attack_class=attack_class)

    def run_full_middleware(self, prompt: str, attack_class: str | None = None) -> PipelineResult:
        started = time.perf_counter()
        prompt_id = str(uuid.uuid4())
        llm_mode = self.llm_mode
        scan = self.scanner.scan(prompt)
        if attack_class:
            scan = scan.__class__(**{**scan.__dict__, "attack_class": attack_class})
        intent = self.intent_classifier.classify(prompt)
        risk = self.risk_engine.decide(scan, intent)
        tool_result = self.gateway.execute(prompt, intent, risk)

        if risk.decision == "block":
            raw_response = f"AIC-SAFE blocked this request. {risk.reason}"
        else:
            raw_response, llm_error = _generate_or_fallback(self.llm_client, self._build_prompt(prompt, risk))
            if tool_result:
                raw_response = f"{raw_response}\n\nTool result: {json.dumps(tool_result.data, default=str)}"
        if risk.decision == "block":
            llm_error = None

        verification = self.output_verifier.verify(raw_response, risk.risk_level)
        reason = f"{risk.reason} {verification.reason}"
        if llm_error:
            reason = f"{reason} LLM latency fallback: {llm_error}"
        latency_ms = int((time.perf_counter() - started) * 1000)
        final_decision = risk.decision if verification.decision == "allow" else verification.decision
        attack_success = _attack_succeeded(final_decision, verification, tool_result)
        event = self._event(
            prompt_id=prompt_id,
            mode="full_middleware",
            source_label="PROTECTED",
            prompt=prompt,
            scan=scan,
            intent=intent,
            risk_level=verification.risk_level,
            decision=final_decision,
            reason=reason,
            tool_result=tool_result,
            final_output=verification.final_text,
            attack_success=attack_success,
            llm_mode=llm_mode,
            latency_ms=latency_ms,
            config_flag_key=risk.config_flag_key,
            output_risk_escalated=verification.output_risk_escalated,
        )
        self.logger.write(event)
        return PipelineResult(
            prompt_id,
            "full_middleware",
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

    def run_rule_only(self, prompt: str, attack_class: str | None = None) -> PipelineResult:
        started = time.perf_counter()
        prompt_id = str(uuid.uuid4())
        scanner = PromptSafetyScanner(use_classifier=False)
        intent_classifier = ToolIntentClassifier(use_classifier=False)
        scan = scanner.scan(prompt)
        if attack_class:
            scan = scan.__class__(**{**scan.__dict__, "attack_class": attack_class})
        intent = intent_classifier.classify(prompt)
        risk = self.risk_engine.decide(scan, intent)
        tool_result = self.gateway.execute(prompt, intent, risk)

        if risk.decision == "block":
            raw_response = f"AIC-SAFE rule-only baseline blocked this request. {risk.reason}"
        else:
            raw_response, llm_error = _generate_or_fallback(self.llm_client, self._build_prompt(prompt, risk))
            if tool_result:
                raw_response = f"{raw_response}\n\nTool result: {json.dumps(tool_result.data, default=str)}"
        if risk.decision == "block":
            llm_error = None

        verification = self.output_verifier.verify(raw_response, risk.risk_level)
        final_decision = risk.decision if verification.decision == "allow" else verification.decision
        reason = f"Rule-only baseline. {risk.reason} {verification.reason}"
        if llm_error:
            reason = f"{reason} LLM latency fallback: {llm_error}"
        latency_ms = int((time.perf_counter() - started) * 1000)
        attack_success = _attack_succeeded(final_decision, verification, tool_result)
        event = self._event(
            prompt_id=prompt_id,
            mode="rule_only",
            source_label="RULE_ONLY",
            prompt=prompt,
            scan=scan,
            intent=intent,
            risk_level=verification.risk_level,
            decision=final_decision,
            reason=reason,
            tool_result=tool_result,
            final_output=verification.final_text,
            attack_success=attack_success,
            llm_mode=self.llm_mode,
            latency_ms=latency_ms,
            config_flag_key=risk.config_flag_key,
            output_risk_escalated=verification.output_risk_escalated,
        )
        self.logger.write(event)
        return PipelineResult(
            prompt_id,
            "rule_only",
            "RULE_ONLY",
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

    def run_raw_llm(self, prompt: str, attack_class: str | None = None) -> PipelineResult:
        return run_raw_llm(prompt, llm_client=self.llm_client, logger=self.logger, attack_class=attack_class)

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
        scan = kwargs.pop("scan")
        intent = kwargs.pop("intent")
        tool_result = kwargs.pop("tool_result", None)
        return {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prompt_text": truncate_prompt(kwargs.pop("prompt")),
            "prompt_safety_label": scan.label,
            "classifier_output": json.dumps(
                {
                    "label": scan.label,
                    "attack_class": scan.attack_class,
                    "risk_score": scan.risk_score,
                    "confidence": scan.confidence,
                    "classifier_available": scan.classifier_available,
                },
                sort_keys=True,
            ),
            "attack_class": scan.attack_class,
            "tool_intent": intent.tool_intent,
            "risk_score": scan.risk_score,
            "tool_usage": _tool_usage(tool_result),
            "final_output": truncate_prompt(kwargs.pop("final_output")),
            **kwargs,
        }


def run_raw_llm(prompt: str, llm_client: object | None = None, logger: SecurityLogger | None = None, attack_class: str | None = None) -> PipelineResult:
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
    raw_response, llm_error = _generate_or_fallback(client, prompt)
    llm_mode = getattr(client, "mode", "unknown")
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
    risk = RiskDecision("low", "allow", "Raw LLM baseline observed scanner output but enforced no controls.")
    reason = "Raw LLM baseline executed without policy, gateway restrictions, or output controls."
    if llm_error:
        reason = f"{reason} LLM latency fallback: {llm_error}"
    attack_success = _attack_succeeded("allow", verification, tool_result)
    event = AICSafePipeline._event(
        prompt_id=prompt_id,
        mode="raw_llm",
        source_label="UNPROTECTED",
        prompt=prompt,
        scan=scan,
        intent=intent,
        risk_level=verification.risk_level,
        decision="allow",
        reason=reason,
        tool_result=tool_result,
        final_output=verification.final_text,
        attack_success=attack_success,
        llm_mode=llm_mode,
        latency_ms=latency_ms,
        config_flag_key=None,
        output_risk_escalated=verification.output_risk_escalated,
    )
    event_logger.write(event)
    return PipelineResult(
        prompt_id,
        "raw_llm",
        "UNPROTECTED",
        prompt,
        scan,
        intent,
        risk,
        llm_mode,
        raw_response,
        tool_result,
        verification,
        latency_ms,
        event,
    )


def run_unprotected(prompt: str, llm_client: object | None = None, logger: SecurityLogger | None = None, attack_class: str | None = None) -> PipelineResult:
    return run_raw_llm(prompt, llm_client=llm_client, logger=logger, attack_class=attack_class)


def _attack_succeeded(decision: str, verification: VerificationResult, tool_result) -> bool:
    return decision == "allow" and (
        verification.sensitive_output
        or bool(tool_result and (tool_result.sensitive_output or tool_result.harmful_action_executed))
    )


def _generate_or_fallback(llm_client: object, prompt: str) -> tuple[str, str | None]:
    try:
        return llm_client.generate(prompt), None
    except (LLMGenerationError, TimeoutError) as exc:
        return (
            "Ollama is still loading or did not respond within the configured latency window. "
            "AIC-SAFE kept Ollama enabled, logged this latency event, and returned this safe fallback response. "
            "Please retry the same prompt after the model finishes warming up.",
            str(exc),
        )


def _tool_usage(tool_result) -> str:
    if not tool_result:
        return ""
    return json.dumps(
        {
            "action": tool_result.action,
            "decision": tool_result.decision,
            "harmful_action_executed": tool_result.harmful_action_executed,
            "sensitive_output": tool_result.sensitive_output,
            "message": tool_result.message,
        },
        sort_keys=True,
    )
