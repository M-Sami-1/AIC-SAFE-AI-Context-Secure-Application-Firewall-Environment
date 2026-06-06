from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


RiskLevel = str
Decision = str
ToolIntent = str


RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


def max_risk(left: RiskLevel, right: RiskLevel) -> RiskLevel:
    return left if RISK_ORDER[left] >= RISK_ORDER[right] else right


@dataclass(frozen=True)
class ScanResult:
    label: str
    risk_score: float
    confidence: float
    matched_patterns: list[str]
    attack_class: str
    reason: str
    classifier_available: bool = False


@dataclass(frozen=True)
class IntentResult:
    tool_intent: ToolIntent
    confidence: float
    matched_patterns: list[str]
    reason: str


@dataclass(frozen=True)
class RiskDecision:
    risk_level: RiskLevel
    decision: Decision
    reason: str
    config_flag_key: str | None = None
    flag_should_proceed: bool = False
    sanitized_on_proceed: bool = True


@dataclass(frozen=True)
class ToolResult:
    action: ToolIntent
    decision: Decision
    message: str
    data: Any = None
    harmful_action_executed: bool = False
    sensitive_output: bool = False


@dataclass(frozen=True)
class VerificationResult:
    final_text: str
    risk_level: RiskLevel
    decision: Decision
    matches: dict[str, list[str]] = field(default_factory=dict)
    redacted: bool = False
    output_risk_escalated: bool = False
    sensitive_output: bool = False
    reason: str = ""


@dataclass(frozen=True)
class PipelineResult:
    prompt_id: str
    mode: str
    source_label: str
    prompt_text: str
    prompt_scan: ScanResult
    intent: IntentResult
    risk: RiskDecision
    llm_mode: str
    llm_response: str
    tool_result: ToolResult | None
    verification: VerificationResult
    latency_ms: int
    event: dict[str, Any]
