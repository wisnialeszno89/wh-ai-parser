from app.agent.agent_action import AgentAction
from app.agent.runtime.browser_action_risk_policy import (
    BrowserActionRiskPolicy,
)


def test_local_risk_policy_overrides_missing_model_confirmation():
    action = AgentAction(
        name="browser_click",
        description="Submit the order.",
        target="Zatwierdź zamówienie",
        requires_confirmation=False,
    )

    required, reason = BrowserActionRiskPolicy.evaluate(action)

    assert required is True
    assert reason is not None


def test_local_risk_policy_allows_ordinary_navigation_controls():
    action = AgentAction(
        name="browser_click",
        description="Continue to the next form step.",
        target="Dalej",
        requires_confirmation=False,
    )

    required, reason = BrowserActionRiskPolicy.evaluate(action)

    assert required is False
    assert reason is None


def test_local_risk_policy_does_not_classify_non_click_browser_actions():
    action = AgentAction(
        name="browser_write_text",
        description="Enter the order reference.",
        target="Numer zamówienia",
        value="ABC-123",
        requires_confirmation=False,
    )

    required, reason = BrowserActionRiskPolicy.evaluate(action)

    assert required is False
    assert reason is None
