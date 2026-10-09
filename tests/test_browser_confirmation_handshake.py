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
class RecordingBrowserProvider:
    page: BrowserPage

    def __post_init__(self):
        self.clicks = 0

    def is_available(self):
        return True

    def current_page(self):
        return self.page

    def open(self, url):
        self.page = replace(self.page, url=url)
        return self.page

    def click(self, target):
        self.clicks += 1
        self.page = BrowserPage(
            url=self.page.url,
            title="Checkout — Submitted",
            text="Zamówienie zostało zatwierdzone.",
            elements=(),
        )
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
                    description="Submit the order after explicit confirmation.",
                    target="Zatwierdź zamówienie",
                    requires_confirmation=True,
                ),
            ),
            rationale="Order submission is confirmation-bound.",
            confidence=0.99,
        )


def create_runtime():
    page = BrowserPage(
        url="https://example.com/checkout",
        title="Checkout",
        text="Oczekuje na potwierdzenie.",
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
    provider = RecordingBrowserProvider(page=page)
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
    return runtime, provider


def test_confirmation_request_can_resume_exact_action_once():
    runtime, provider = create_runtime()
    session_id = "confirmation-session"

    blocked = runtime.run(
        AgentRequest(
            message="Zatwierdź moje zamówienie.",
            session_id=session_id,
            metadata={"target_application": "Browser"},
        )
    )

    assert blocked.requires_manual_review is True
    assert blocked.control_loop_result is not None
    assert blocked.control_loop_result.executed_actions == 0
    assert blocked.confirmation_request is not None
    assert (
        blocked.confirmation_request.session_id
        == session_id
    )
    assert (
        blocked.confirmation_request.action_name
        == "browser_click"
    )
    assert (
        blocked.confirmation_request.target
        == "Zatwierdź zamówienie"
    )
    assert provider.clicks == 0

    approved = runtime.run(
        AgentRequest(
            message="Zatwierdź moje zamówienie.",
            session_id=session_id,
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
    assert approved.control_loop_result.executed_actions == 1
    assert approved.confirmation_request is None
    assert provider.clicks == 1

    reused = runtime.run(
        AgentRequest(
            message="Zatwierdź moje zamówienie.",
            session_id=session_id,
            metadata={
                "target_application": "Browser",
                "confirmation_token": (
                    blocked.confirmation_request.token
                ),
            },
        )
    )

    assert reused.requires_manual_review is True
    assert reused.executed is False
    assert reused.control_loop_result is None
    assert (
        reused.context.get_value("task_reasoning_failure")
        == "invalid_or_expired_confirmation_token"
    )
    assert provider.clicks == 1
