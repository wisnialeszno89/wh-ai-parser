from dataclasses import dataclass

from app.agent.adapters.browser_adapter import (
    BrowserAdapter,
    BrowserElement,
    BrowserPage,
)
from app.agent.agent_intent import AgentIntent
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
class FakeBrowserProvider:
    page: BrowserPage
    available: bool = True

    def __post_init__(self):
        self.clicks = []

    def is_available(self):
        return self.available

    def open(self, url):
        return self.page

    def current_page(self):
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


class ConfirmationReasoner(TaskReasoner):
    def reason(self, context):
        return ReasoningProposal(
            actions=(
                ReasoningAction(
                    name="browser_click",
                    description="Click the final submission control.",
                    target="Zatwierdź zamówienie",
                    requires_confirmation=True,
                ),
            ),
            rationale="Submitting the order is a confirmation-bound action.",
            confidence=0.99,
        )


def create_page():
    return BrowserPage(
        url="https://example.com/checkout",
        title="Checkout",
        text="Potwierdź zamówienie",
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


def test_browser_confirmation_boundary_blocks_action_before_executor():
    page = create_page()
    provider = FakeBrowserProvider(page=page)
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

    result = runtime.run(
        AgentRequest(
            message="Zatwierdź moje zamówienie.",
            metadata={
                "target_application": "Browser",
            },
        )
    )

    assert result.intent == AgentIntent.COMPUTER_USE
    assert result.executed is True
    assert result.requires_manual_review is True
    assert result.control_loop_result is not None
    assert result.control_loop_result.requires_manual_review is True
    assert result.control_loop_result.stopped is True
    assert result.control_loop_result.executed_actions == 0
    assert provider.clicks == []
