from __future__ import annotations

import config
from aic_safe.types import IntentResult, RiskDecision, ScanResult


class RiskDecisionEngine:
    def decide(self, scan: ScanResult, intent: IntentResult) -> RiskDecision:
        if scan.risk_score >= config.RISK_THRESHOLDS["block_score"] or scan.label == "attack":
            return RiskDecision(
                risk_level="high",
                decision="block",
                reason=f"Blocked high-risk prompt. {scan.reason}",
            )

        if scan.risk_score >= config.RISK_THRESHOLDS["flag_score"] or scan.label == "suspicious":
            config_key = f"flag_policy.{intent.tool_intent}"
            policy = config.FLAG_POLICY.get(intent.tool_intent, config.FLAG_POLICY["none"])
            if policy.get("proceed", False):
                reason = (
                    f"Flagged medium-risk prompt; {config_key}.proceed=True allows a controlled "
                    "sanitized path."
                )
            else:
                reason = f"Flagged medium-risk prompt; {config_key}.proceed=False holds the action."
            return RiskDecision(
                risk_level="medium",
                decision="flag",
                reason=reason,
                config_flag_key=config_key,
                flag_should_proceed=bool(policy.get("proceed", False)),
                sanitized_on_proceed=bool(policy.get("sanitized", True)),
            )

        return RiskDecision(
            risk_level="low",
            decision="allow",
            reason="Allowed low-risk prompt after scanner and intent checks.",
        )
