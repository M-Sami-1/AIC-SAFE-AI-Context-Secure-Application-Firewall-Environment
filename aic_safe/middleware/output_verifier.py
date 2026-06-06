from __future__ import annotations

from aic_safe.types import VerificationResult, max_risk

from .dlp import DLPScanner


class OutputVerifier:
    def __init__(self) -> None:
        self.dlp = DLPScanner()

    def verify(self, text: str, input_risk_level: str) -> VerificationResult:
        matches = self.dlp.scan(text)
        output_risk = self.dlp.risk_for_matches(matches)
        final_risk = max_risk(input_risk_level, output_risk)
        escalated = final_risk != input_risk_level and output_risk != "low"
        if final_risk == "high" and matches:
            return VerificationResult(
                final_text="Output blocked by AIC-SAFE DLP because high-risk sensitive content was detected.",
                risk_level=final_risk,
                decision="block",
                matches=matches,
                output_risk_escalated=escalated,
                sensitive_output=True,
                reason="DLP detected high-risk sensitive output.",
            )
        if matches:
            return VerificationResult(
                final_text=self.dlp.redact(text, matches),
                risk_level=final_risk,
                decision="redact",
                matches=matches,
                redacted=True,
                output_risk_escalated=escalated,
                sensitive_output=True,
                reason="DLP redacted sensitive output patterns.",
            )
        return VerificationResult(
            final_text=text,
            risk_level=final_risk,
            decision="allow",
            matches={},
            reason="No additional output violations detected.",
        )
