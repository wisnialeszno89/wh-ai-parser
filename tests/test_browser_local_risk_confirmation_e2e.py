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
class RiskConfirmationProvider:
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
        self.page = replace(
            self.page,
            title="Submitted",
            text="Zamówienie zatwierdzone.",
            elements=(),
        )
        return self.page

    def write_text(self, target, value):
        return self.page

    def select_option(self, target, value):
        return self.page

    def back(self):
        return self.page


class ModelOmitsConfirmationReasoner(TaskReasoner):
    def reason(self, context):
        return ReasoningProposal(
            actions=(
                ReasoningAction(
                    name="browser_click",
                    description="Submit the order.",
                    target="Zatwierdź zamówienie",
                    requires_confirmation=False,
                ),
            ),
            rationale=(
                "The model intentionally omits the confirmation flag; "
                "the local risk policy must enforce it."
            ),
            confidence=0.99,
        )


def create_runtime():
    page = BrowserPage(
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

    provider = RiskConfirmationProvider(page=page)
    adapter = BrowserAdapter(
        provider=provider,
        allowed_domains=("example.com",),
        dry_run=False,
    )
    runtime = AgentRuntime(
        orchestrator=AgentOrchestrator(
            task_reasoner=ModelOmitsConfirmationReasoner(),
            require_task_reasoning=True,
        ),
        control_loop=create_browser_agent_control_loop(
            browser_adapter=adapter,
        ),
        browser_adapter=adapter,
        browser_context_enabled=True,
    )

    return runtime, provider


def test_local_risk_policy_requires_confirmation_then_resumes_exact_action():
    runtime, provider = create_runtime()

    blocked = runtime.run(
        AgentRequest(
            message="Zatwierdź moje zamówienie.",
            session_id="risk-confirmation-e2e",
            metadata={"target_application": "Browser"},
        )
    )

    assert blocked.requires_manual_review is True
    assert blocked.control_loop_result is not None
    assert blocked.control_loop_result.executed_actions == 0
    assert blocked.confirmation_request is not None
    assert blocked.confirmation_request.target == "Zatwierdź zamówienie"
    assert provider.clicks == []

    approved = runtime.run(
        AgentRequest(
            message="Zatwierdź moje zamówienie.",
            session_id="risk-confirmation-e2e",
            metadata={
                "target_application": "Browser",
                "confirmation_token": blocked.confirmation_request.token,
            },
        )
    )

    assert approved.requires_manual_review is False
    assert approved.control_loop_result is not None
    assert approved.control_loop_result.success is True
    assert approved.control_loop_result.executed_actions == 1
    assert provider.clicks == ["Zatwierdź zamówienie"]
