from aic_safe.middleware.gateway import ToolGateway
from aic_safe.types import IntentResult, RiskDecision


def test_gateway_holds_flagged_export_by_config():
    gateway = ToolGateway()
    intent = IntentResult("export_data", 0.9, [], "test")
    risk = RiskDecision(
        risk_level="medium",
        decision="flag",
        reason="test",
        config_flag_key="flag_policy.export_data",
        flag_should_proceed=False,
    )
    result = gateway.execute("export all records", intent, risk)
    assert result is not None
    assert result.decision == "flag"
    assert result.data is None
