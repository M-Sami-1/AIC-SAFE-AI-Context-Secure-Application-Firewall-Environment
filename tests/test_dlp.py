from aic_safe.middleware.output_verifier import OutputVerifier


def test_output_verifier_escalates_and_blocks_secret():
    result = OutputVerifier().verify("api_key=AICSAFE_DEMO_KEY_123456", "low")
    assert result.risk_level == "high"
    assert result.decision == "block"
    assert result.output_risk_escalated is True
