from __future__ import annotations

from aic_safe.tools.database_tool import read_business_data
from aic_safe.tools.export_tool import export_data
from aic_safe.tools.fake_api_cloud_tool import run_fake_cloud_action
from aic_safe.tools.mock_email_tool import send_mock_email
from aic_safe.types import IntentResult, RiskDecision, ToolResult


class ToolGateway:
    """Zero-trust gateway for every environment-facing action."""

    def execute(self, prompt: str, intent: IntentResult, risk: RiskDecision) -> ToolResult | None:
        action = intent.tool_intent
        if action == "none":
            return None
        if risk.decision == "block":
            return ToolResult(action, "block", f"Blocked {action}: {risk.reason}")
        if risk.decision == "flag" and not risk.flag_should_proceed:
            return ToolResult(action, "flag", f"Held {action}: {risk.reason}")

        sanitized = risk.decision == "flag" or risk.sanitized_on_proceed
        if action == "db_read":
            data = read_business_data(sanitized=sanitized)
            return ToolResult(action, risk.decision, "Database read returned a controlled result.", data)
        if action == "send_email":
            data = send_mock_email(prompt, sanitized=sanitized)
            return ToolResult(action, risk.decision, "Mock email action simulated.", data)
        if action == "export_data":
            data = export_data(sanitized=sanitized)
            return ToolResult(action, risk.decision, "Export action returned safe demo data.", data)
        if action == "fake_api_cloud_action":
            data = run_fake_cloud_action(prompt, sanitized=sanitized)
            return ToolResult(action, risk.decision, "Fake API/cloud action simulated.", data)
        return ToolResult(action, "block", f"Unknown action {action} blocked by default.")


def execute_unprotected_action(prompt: str, intent: IntentResult) -> ToolResult | None:
    action = intent.tool_intent
    if action == "none":
        return None
    if action == "db_read":
        data = read_business_data(sanitized=False)
        return ToolResult(action, "allow", "Unprotected database read executed.", data, sensitive_output=True)
    if action == "send_email":
        data = send_mock_email(prompt, sanitized=False)
        return ToolResult(action, "allow", "Unprotected mock email action executed.", data, harmful_action_executed=True)
    if action == "export_data":
        data = export_data(sanitized=False)
        return ToolResult(action, "allow", "Unprotected export executed.", data, harmful_action_executed=True, sensitive_output=True)
    if action == "fake_api_cloud_action":
        data = run_fake_cloud_action(prompt, sanitized=False)
        return ToolResult(action, "allow", "Unprotected fake API/cloud action executed.", data, harmful_action_executed=True)
    return None
