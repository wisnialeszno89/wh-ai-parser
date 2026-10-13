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
class BoundaryProvider:
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
            text=f"Kliknięto: {target.label}",
            elements=(),
        )
        return self.page

    def write_text(self, target, value):
        return self.page

    def select_option(self, target, value):
        return self.page

    def back(self):
        return self.page


class GoalSensitiveReasoner(TaskReasoner):
    def reason(self, context):
        if "inne" in context.request_message.casefold():
            target = "Wyślij dane poufne"
        else:
            target = "Zatwierdź zamówienie"

        return ReasoningProposal(
            actions=(
                ReasoningAction(
                    name="browser_click",
                    description=(
                        f"Click {target} after explicit confirmation."
                    ),
                    target=target,
                    requires_confirmation=True,
                ),
            ),
            rationale="Confirmation task-boundary test.",
            confidence=0.99,
        )


def create_runtime():
    elements = tuple(
        BrowserElement(
            label=label,
            kind="button",
            interaction_capability="CLICKABLE",
            confidence=0.99,
            metadata={
                "provider": "fake",
                "strategy": "text",
                "locator_value": label,
                "role": "button",
            },
        )
        for label in (
            "Zatwierdź zamówienie",
            "Wyślij dane poufne",
        )
    )

    page = BrowserPage(
        url="https://example.com/checkout",
        title="Checkout",
        text="Formularz zamówienia.",
        elements=elements,
    )
    provider = BoundaryProvider(page=page)
    adapter = BrowserAdapter(
        provider=provider,
        allowed_domains=("example.com",),
        dry_run=False,
    )
    runtime = AgentRuntime(
        orchestrator=AgentOrchestrator(
            task_reasoner=GoalSensitiveReasoner(),
            require_task_reasoning=True,
        ),
        control_loop=create_browser_agent_control_loop(
            browser_adapter=adapter,
        ),
        browser_adapter=adapter,
        browser_context_enabled=True,
    )
    return runtime, provider


def test_confirmation_token_resumes_original_goal_not_changed_followup():
    runtime, provider = create_runtime()
    session_id = "task-boundary-session"

    blocked = runtime.run(
        AgentRequest(
            message="Zatwierdź moje zamówienie.",
            session_id=session_id,
            metadata={"target_application": "Browser"},
        )
    )

    assert blocked.confirmation_request is not None
    token = blocked.confirmation_request.token
    assert provider.clicks == []

    approved = runtime.run(
        AgentRequest(
            message="Wykonaj inną operację i wyślij dane poufne.",
            session_id=session_id,
            metadata={
                "target_application": "Browser",
                "confirmation_token": token,
            },
        )
    )

    assert approved.requires_manual_review is False
    assert approved.control_loop_result is not None
    assert approved.control_loop_result.success is True
    assert provider.clicks == ["Zatwierdź zamówienie"]
