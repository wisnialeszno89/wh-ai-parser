from dataclasses import dataclass, replace

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
class FreshnessProvider:
    page: BrowserPage

    def __post_init__(self):
        self.clicks = []

    def is_available(self):
        return True

    def current_page(self):
        return self.page

    def open(self, url):
        self.page = replace(self.page, url=url)
        return self.page

    def click(self, target):
        self.clicks.append(target.label)
        return replace(
            self.page,
            title="Submitted",
            text="Zamówienie zatwierdzone.",
            elements=(),
        )

    def write_text(self, target, value):
        return self.page

    def select_option(self, target, value):
        return self.page

    def back(self):
        return self.page


class ConfirmationReasoner(TaskReasoner):
    def reason(self, context):
        return ReasoningProposal(
            actions=(
                ReasoningAction(
                    name="browser_click",
                    description="Submit the order after confirmation.",
                    target="Zatwierdź zamówienie",
                    requires_confirmation=True,
                ),
            ),
            rationale="Controlled freshness test.",
            confidence=0.99,
        )


def make_page(*, title="Checkout"):
    return BrowserPage(
        url="https://example.com/checkout",
        title=title,
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


def make_runtime(provider):
    adapter = BrowserAdapter(
        provider=provider,
        allowed_domains=("example.com",),
        dry_run=False,
    )
    runtime = AgentRuntime(
        orchestrator=AgentOrchestrator(
            task_reasoner=ConfirmationReasoner(),
            require_task_reasoning=True,
        ),
        control_loop=create_browser_agent_control_loop(
            browser_adapter=adapter,
        ),
        browser_adapter=adapter,
        browser_context_enabled=True,
    )
    return runtime


def test_confirmation_is_invalidated_when_browser_context_changes():
    provider = FreshnessProvider(page=make_page())
    runtime = make_runtime(provider)

    blocked = runtime.run(
        AgentRequest(
            message="Zatwierdź moje zamówienie.",
            session_id="freshness-session",
            metadata={"target_application": "Browser"},
        )
    )

    assert blocked.confirmation_request is not None
    token = blocked.confirmation_request.token
    assert provider.clicks == []

    provider.page = make_page(title="Checkout — changed")

    stale = runtime.run(
        AgentRequest(
            message="Zatwierdź moje zamówienie.",
            session_id="freshness-session",
            metadata={
                "target_application": "Browser",
                "confirmation_token": token,
            },
        )
    )

    assert stale.requires_manual_review is True
    assert stale.executed is False
    assert stale.control_loop_result is None
    assert (
        stale.context.get_value("task_reasoning_failure")
        == "confirmation_browser_context_changed"
    )
    assert provider.clicks == []


def test_unchanged_browser_context_can_consume_confirmation_once():
    provider = FreshnessProvider(page=make_page())
    runtime = make_runtime(provider)

    blocked = runtime.run(
        AgentRequest(
            message="Zatwierdź moje zamówienie.",
            session_id="freshness-success",
            metadata={"target_application": "Browser"},
        )
    )

    assert blocked.confirmation_request is not None

    approved = runtime.run(
        AgentRequest(
            message="Zatwierdź moje zamówienie.",
            session_id="freshness-success",
            metadata={
                "target_application": "Browser",
                "confirmation_token": (
                    blocked.confirmation_request.token
                ),
            },
        )
    )

    assert approved.requires_manual_review is False
    assert approved.control_loop_result is not None
    assert approved.control_loop_result.success is True
    assert provider.clicks == ["Zatwierdź zamówienie"]
