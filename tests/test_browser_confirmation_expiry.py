from dataclasses import dataclass

from app.agent.adapters.browser_adapter import (
    BrowserAdapter,
    BrowserElement,
    BrowserPage,
)
from app.agent.agent_request import AgentRequest
from app.agent.reasoning.reasoning_action import ReasoningAction
from app.agent.reasoning.reasoning_proposal import ReasoningProposal
from app.agent.reasoning.task_reasoner import TaskReasoner
from app.agent.runtime.agent_orchestrator import AgentOrchestrator
from app.agent.runtime.agent_runtime import AgentRuntime
from app.agent.runtime.browser_agent_control_loop import (
    create_browser_agent_control_loop,
)


@dataclass
class Clock:
    now: float = 100.0

    def __call__(self):
        return self.now


@dataclass
class ExpiryProvider:
    page: BrowserPage

    def __post_init__(self):
        self.clicks = []

    def is_available(self):
        return True

    def current_page(self):
        return self.page

    def open(self, url):
        return self.page

    def click(self, target):
        self.clicks.append(target.label)
        return self.page

    def write_text(self, target, value):
        return self.page

    def select_option(self, target, value):
        return self.page

    def back(self):
        return self.page


class CountingReasoner(TaskReasoner):
    def __init__(self):
        self.calls = 0

    def reason(self, context):
        self.calls += 1
        return ReasoningProposal(
            actions=(
                ReasoningAction(
                    name="browser_click",
                    description="Submit the order after confirmation.",
                    target="Zatwierdź zamówienie",
                    requires_confirmation=True,
                ),
            ),
            rationale="Confirmation expiry test.",
            confidence=0.99,
        )


def make_page():
    return BrowserPage(
        url="https://example.com/checkout",
        title="Checkout",
        text="Formularz zamówienia.",
        elements=(
            BrowserElement(
                label="Zatwierdź zamówienie",
                kind="button",
                interaction_capability="CLICKABLE",
                confidence=0.99,
                metadata={
                    "provider": "fake",
                    "strategy": "text",
                    "locator_value": "Zatwierdź zamówienie",
                    "role": "button",
                },
            ),
        ),
    )


def make_runtime(reasoner, clock):
    provider = ExpiryProvider(page=make_page())
    adapter = BrowserAdapter(
        provider=provider,
        allowed_domains=("example.com",),
        dry_run=False,
    )
    runtime = AgentRuntime(
        orchestrator=AgentOrchestrator(
            task_reasoner=reasoner,
            require_task_reasoning=True,
        ),
        control_loop=create_browser_agent_control_loop(
            browser_adapter=adapter,
        ),
        browser_adapter=adapter,
        browser_context_enabled=True,
        confirmation_ttl_seconds=10.0,
        confirmation_clock=clock,
    )
    return runtime, provider


def test_expired_confirmation_fails_before_reasoning_and_execution():
    clock = Clock()
    reasoner = CountingReasoner()
    runtime, provider = make_runtime(reasoner, clock)

    blocked = runtime.run(
        AgentRequest(
            message="Zatwierdź moje zamówienie.",
            session_id="expiry-session",
            metadata={"target_application": "Browser"},
        )
    )

    assert blocked.confirmation_request is not None
    token = blocked.confirmation_request.token
    assert reasoner.calls == 1
    assert provider.clicks == []

    clock.now = 110.0

    expired = runtime.run(
        AgentRequest(
            message="Zatwierdź moje zamówienie.",
            session_id="expiry-session",
            metadata={
                "target_application": "Browser",
                "confirmation_token": token,
            },
        )
    )

    assert expired.requires_manual_review is True
    assert expired.executed is False
    assert expired.control_loop_result is None
    assert (
        expired.context.get_value("task_reasoning_failure")
        == "invalid_or_expired_confirmation_token"
    )
    assert reasoner.calls == 1
    assert provider.clicks == []


def test_confirmation_ttl_rejects_non_positive_configuration():
    reasoner = CountingReasoner()
    clock = Clock()

    try:
        make_runtime(reasoner, clock)
    except Exception:
        pass

    # Exercise the public constructor validation directly without requiring
    # a browser provider.
    try:
        AgentRuntime(confirmation_ttl_seconds=0)
    except ValueError as exc:
        assert str(exc) == "confirmation_ttl_seconds must be greater than zero."
    else:
        raise AssertionError("Expected invalid confirmation TTL to fail.")
