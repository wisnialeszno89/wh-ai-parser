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
class ScopeExecutionProvider:
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
        if target.label == "Dalej":
            self.page = replace(
                self.page,
                title="Checkout — step 2",
                text="Przejdź do zatwierdzenia.",
            )
        else:
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


class MultiStepReasoner(TaskReasoner):
    def reason(self, context):
        return ReasoningProposal(
            actions=(
                ReasoningAction(
                    name="browser_click",
                    description="Continue to the order confirmation.",
                    target="Dalej",
                    requires_confirmation=False,
                ),
                ReasoningAction(
                    name="browser_click",
                    description="Submit the order after confirmation.",
                    target="Zatwierdź zamówienie",
                    requires_confirmation=True,
                ),
            ),
            rationale="Resume must be scoped to the approved action.",
            confidence=0.99,
        )


def create_runtime():
    page = BrowserPage(
        url="https://example.com/checkout",
        title="Checkout",
        text="Formularz zamówienia.",
        elements=(
            BrowserElement(
                label="Dalej",
                kind="button",
                interaction_capability="CLICKABLE",
                confidence=0.99,
                metadata={
                    "provider": "fake",
                    "strategy": "text",
                    "locator_value": "Dalej",
                    "role": "button",
                },
            ),
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
    provider = ScopeExecutionProvider(page=page)
    adapter = BrowserAdapter(
        provider=provider,
        allowed_domains=("example.com",),
        dry_run=False,
    )
    runtime = AgentRuntime(
        orchestrator=AgentOrchestrator(
            task_reasoner=MultiStepReasoner(),
            require_task_reasoning=True,
        ),
        control_loop=create_browser_agent_control_loop(
            browser_adapter=adapter,
        ),
        browser_adapter=adapter,
        browser_context_enabled=True,
    )
    return runtime, provider


def test_confirmation_resume_does_not_replay_prior_steps():
    runtime, provider = create_runtime()

    blocked = runtime.run(
        AgentRequest(
            message="Przejdź dalej i zatwierdź moje zamówienie.",
            session_id="scope-execution-session",
            metadata={"target_application": "Browser"},
        )
    )

    assert blocked.confirmation_request is not None
    token = blocked.confirmation_request.token
    assert provider.clicks == ["Dalej"]

    approved = runtime.run(
        AgentRequest(
            message="Przejdź dalej i zatwierdź moje zamówienie.",
            session_id="scope-execution-session",
            metadata={
                "target_application": "Browser",
                "confirmation_token": token,
            },
        )
    )

    assert approved.requires_manual_review is False
    assert approved.control_loop_result is not None
    assert approved.control_loop_result.success is True
    assert provider.clicks == ["Dalej", "Zatwierdź zamówienie"]
