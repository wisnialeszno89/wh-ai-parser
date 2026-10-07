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
class ScopeProvider:
    page: BrowserPage

    def __post_init__(self):
        self.clicks = []
        self.writes = []

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
            text="Wysłano.",
            elements=(),
        )
        return self.page

    def write_text(self, target, value):
        self.writes.append((target.label, value))
        self.page = replace(
            self.page,
            elements=tuple(
                replace(
                    element,
                    current_value=value,
                )
                if element.label == target.label
                else element
                for element in self.page.elements
            ),
        )
        return self.page

    def select_option(self, target, value):
        return self.page

    def back(self):
        return self.page


class ScopedReasoner(TaskReasoner):
    def __init__(self, actions):
        self.actions = list(actions)
        self.calls = 0

    def reason(self, context):
        index = min(self.calls, len(self.actions) - 1)
        action = self.actions[index]
        self.calls += 1
        return ReasoningProposal(
            actions=(action,),
            rationale="Controlled confirmation scope test.",
            confidence=0.99,
        )


def create_runtime(reasoner):
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
            BrowserElement(
                label="Wyślij dane poufne",
                kind="button",
                interaction_capability="CLICKABLE",
                confidence=0.99,
                metadata={
                    "provider": "fake",
                    "strategy": "text",
                    "locator_value": "Wyślij dane poufne",
                    "role": "button",
                },
            ),
        ),
    )
    provider = ScopeProvider(page=page)
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
    )
    return runtime, provider


def confirm_click(label):
    return ReasoningAction(
        name="browser_click",
        description=f"Click {label} after explicit confirmation.",
        target=label,
        requires_confirmation=True,
    )


def test_confirmation_token_cannot_authorize_different_target():
    reasoner = ScopedReasoner(
        [
            confirm_click("Zatwierdź zamówienie"),
            confirm_click("Wyślij dane poufne"),
            confirm_click("Zatwierdź zamówienie"),
        ]
    )
    runtime, provider = create_runtime(reasoner)
    session_id = "scope-session"

    blocked = runtime.run(
        AgentRequest(
            message="Wykonaj wskazaną operację.",
            session_id=session_id,
            metadata={"target_application": "Browser"},
        )
    )
    token = blocked.confirmation_request.token

    wrong = runtime.run(
        AgentRequest(
            message="Wykonaj wskazaną operację.",
            session_id=session_id,
            metadata={
                "target_application": "Browser",
                "confirmation_token": token,
            },
        )
    )

    assert wrong.requires_manual_review is True
    assert wrong.executed is False
    assert (
        wrong.context.get_value("task_reasoning_failure")
        == "confirmation_token_action_mismatch"
    )
    assert provider.clicks == []

    correct = runtime.run(
        AgentRequest(
            message="Wykonaj wskazaną operację.",
            session_id=session_id,
            metadata={
                "target_application": "Browser",
                "confirmation_token": token,
            },
        )
    )

    assert correct.requires_manual_review is False
    assert correct.control_loop_result is not None
    assert correct.control_loop_result.success is True
    assert provider.clicks == ["Zatwierdź zamówienie"]


def test_confirmation_token_cannot_authorize_changed_write_value():
    initial = ReasoningAction(
        name="browser_write_text",
        description="Enter Adam after explicit confirmation.",
        target="Imię",
        value="Adam",
        requires_confirmation=True,
    )
    changed = ReasoningAction(
        name="browser_write_text",
        description="Enter Ewa after explicit confirmation.",
        target="Imię",
        value="Ewa",
        requires_confirmation=True,
    )

    page_reasoner = ScopedReasoner([initial, changed, initial])
    page = BrowserPage(
        url="https://example.com/form",
        title="Form",
        text="Formularz.",
        elements=(
            BrowserElement(
                label="Imię",
                kind="textbox",
                interaction_capability="EDITABLE",
                confidence=0.99,
                metadata={
                    "provider": "fake",
                    "strategy": "label",
                    "locator_value": "Imię",
                    "role": "textbox",
                },
            ),
        ),
    )
    provider = ScopeProvider(page=page)
    adapter = BrowserAdapter(
        provider=provider,
        allowed_domains=("example.com",),
        dry_run=False,
    )
    runtime = AgentRuntime(
        orchestrator=AgentOrchestrator(
            task_reasoner=page_reasoner,
            require_task_reasoning=True,
        ),
        control_loop=create_browser_agent_control_loop(
            browser_adapter=adapter,
        ),
        browser_adapter=adapter,
        browser_context_enabled=True,
    )

    blocked = runtime.run(
        AgentRequest(
            message="Wpisz imię Adam.",
            session_id="write-scope",
            metadata={"target_application": "Browser"},
        )
    )
    token = blocked.confirmation_request.token

    changed_result = runtime.run(
        AgentRequest(
            message="Wpisz inną wartość.",
            session_id="write-scope",
            metadata={
                "target_application": "Browser",
                "confirmation_token": token,
            },
        )
    )

    assert changed_result.requires_manual_review is True
    assert (
        changed_result.context.get_value("task_reasoning_failure")
        == "confirmation_token_action_mismatch"
    )
    assert provider.writes == []

    approved = runtime.run(
        AgentRequest(
            message="Wpisz imię Adam.",
            session_id="write-scope",
            metadata={
                "target_application": "Browser",
                "confirmation_token": token,
            },
        )
    )

    assert approved.requires_manual_review is False
    assert approved.control_loop_result is not None
    assert approved.control_loop_result.success is True
    assert provider.writes == [("Imię", "Adam")]


def test_wrong_session_does_not_consume_valid_confirmation_token():
    action = confirm_click("Zatwierdź zamówienie")
    reasoner = ScopedReasoner([action, action, action])
    runtime, provider = create_runtime(reasoner)

    blocked = runtime.run(
        AgentRequest(
            message="Potwierdź zamówienie.",
            session_id="owner-session",
            metadata={"target_application": "Browser"},
        )
    )
    token = blocked.confirmation_request.token

    wrong_session = runtime.run(
        AgentRequest(
            message="Potwierdź zamówienie.",
            session_id="attacker-session",
            metadata={
                "target_application": "Browser",
                "confirmation_token": token,
            },
        )
    )

    assert wrong_session.requires_manual_review is True
    assert (
        wrong_session.context.get_value("task_reasoning_failure")
        == "confirmation_token_session_mismatch"
    )
    assert provider.clicks == []

    approved = runtime.run(
        AgentRequest(
            message="Potwierdź zamówienie.",
            session_id="owner-session",
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
