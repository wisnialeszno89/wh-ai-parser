from dataclasses import dataclass

from app.agent.adapters.browser_adapter import (
    BrowserAdapter,
    BrowserElement,
    BrowserPage,
)
from app.agent.agent_action import AgentAction
from app.agent.agent_request import AgentRequest
from app.agent.bridge.world_state import WorldState
from app.agent.execution.browser_action_executor import BrowserActionExecutor
from app.agent.execution.execution_engine import ExecutionEngine
from app.agent.execution.execution_result import ExecutionResult
from app.agent.execution.executor_registry import ExecutorRegistry
from app.agent.reasoning.reasoning_action import ReasoningAction
from app.agent.reasoning.reasoning_proposal import ReasoningProposal
from app.agent.reasoning.reasoning_task_planner import ReasoningTaskPlanner
from app.agent.reasoning.task_planning_context import TaskPlanningContext
from app.agent.reasoning.task_reasoner import TaskReasoner
from app.agent.runtime.execution_context import ExecutionContext
from app.agent.runtime.verification_loop import VerificationLoop
from app.agent.verification.expectation_resolver import ExpectationResolver
from app.agent.verification.outcome_verifier import OutcomeVerifier


@dataclass
class FakeBrowserProvider:
    page: BrowserPage
    available: bool = True

    def __post_init__(self):
        self.opened = []
        self.clicks = []
        self.writes = []
        self.selections = []
        self.back_count = 0

    def is_available(self):
        return self.available

    def open(self, url):
        self.opened.append(url)
        return self.page

    def current_page(self):
        return self.page

    def click(self, target):
        self.clicks.append(target.label)
        return self.page

    def write_text(self, target, value):
        self.writes.append((target.label, value))
        return self.page

    def select_option(self, target, value):
        self.selections.append((target.label, value))
        return self.page

    def back(self):
        self.back_count += 1
        return self.page


def create_page(*, duplicate_button=False, redirected_url=None):
    elements = [
        BrowserElement(
            label="Zatwierdź",
            kind="button",
            interaction_capability="CLICKABLE",
            confidence=0.99,
        ),
        BrowserElement(
            label="Imię klienta",
            kind="textbox",
            interaction_capability="EDITABLE",
            current_value="",
            confidence=0.99,
        ),
        BrowserElement(
            label="Kraj",
            kind="combobox",
            interaction_capability="SELECTABLE",
            current_value="",
            confidence=0.99,
        ),
    ]

    if duplicate_button:
        elements.append(
            BrowserElement(
                label="Zatwierdź",
                kind="button",
                interaction_capability="CLICKABLE",
                confidence=0.98,
            )
        )

    return BrowserPage(
        url=redirected_url or "https://example.com/form",
        title="Test form",
        text="Kontrolowany formularz",
        elements=tuple(elements),
    )


def create_adapter(
    *,
    page=None,
    dry_run=False,
    allowed_domains=("example.com",),
):
    provider = FakeBrowserProvider(
        page=page or create_page(),
    )
    adapter = BrowserAdapter(
        provider=provider,
        allowed_domains=allowed_domains,
        dry_run=dry_run,
    )
    return adapter, provider


def create_context(page=None):
    page = page or create_page()
    return ExecutionContext(
        request=AgentRequest(message="browser safety test"),
        data={
            "browser_page": page,
        },
    )


def create_browser_planning_context(page=None):
    page = page or create_page()
    return TaskPlanningContext(
        request_message="Kliknij Zatwierdź",
        intent="computer_use",
        browser_page=page,
        world=WorldState.from_browser_page(page),
    )


def test_browser_executor_stops_without_clicking_missing_target():
    adapter, provider = create_adapter()
    executor = BrowserActionExecutor(adapter)

    result = executor.execute(
        AgentAction(
            name="browser_click",
            description="Click the requested control.",
            target="Nieistniejący przycisk",
        ),
        create_context(),
    )

    assert result.success is False
    assert result.requires_manual_review is False
    assert provider.clicks == []


def test_browser_executor_stops_on_ambiguous_semantic_target():
    adapter, provider = create_adapter(
        page=create_page(duplicate_button=True),
    )
    executor = BrowserActionExecutor(adapter)

    result = executor.execute(
        AgentAction(
            name="browser_click",
            description="Click the requested control.",
            target="Zatwierdź",
        ),
        create_context(
            page=create_page(duplicate_button=True),
        ),
    )

    assert result.success is False
    assert provider.clicks == []


def test_browser_executor_rejects_low_level_target_without_provider_call():
    adapter, provider = create_adapter()
    executor = BrowserActionExecutor(adapter)

    result = executor.execute(
        AgentAction(
            name="browser_click",
            description="Click the requested control.",
            target="css=#submit",
        ),
        create_context(),
    )

    assert result.success is False
    assert provider.clicks == []


def test_browser_adapter_rejects_resulting_page_outside_allowed_domains():
    page = create_page(
        redirected_url="https://evil.example.net/landing",
    )
    adapter, provider = create_adapter(page=page)

    result_raises = None
    try:
        adapter.open("https://example.com/form")
    except PermissionError as exc:
        result_raises = exc

    assert result_raises is not None
    assert provider.opened == ["https://example.com/form"]


def test_reasoning_planner_rejects_zero_confidence_before_action():
    class ZeroConfidenceReasoner(TaskReasoner):
        def reason(self, context):
            return ReasoningProposal(
                actions=(
                    ReasoningAction(
                        name="browser_click",
                        description="Click the visible submit control.",
                        target="Zatwierdź",
                    ),
                ),
                rationale="No confidence must fail closed.",
                confidence=0.0,
            )

    page = create_page()
    planner = ReasoningTaskPlanner(ZeroConfidenceReasoner())

    assert planner.plan(
        context=create_browser_planning_context(page),
    ) is None
    assert planner.last_failure_reason == "non_positive_confidence"


def test_reasoning_planner_rejects_browser_action_without_live_target():
    class WrongTargetReasoner(TaskReasoner):
        def reason(self, context):
            return ReasoningProposal(
                actions=(
                    ReasoningAction(
                        name="browser_click",
                        description="Click the requested control.",
                        target="Potwierdź",
                    ),
                ),
                rationale="Target is not present in the observed page.",
                confidence=0.95,
            )

    planner = ReasoningTaskPlanner(WrongTargetReasoner())

    assert planner.plan(
        context=create_browser_planning_context(),
    ) is None
    assert planner.last_failure_reason == "target_not_visible_in_scene"


def test_reasoning_planner_rejects_browser_action_without_browser_context():
    class BrowserReasoner(TaskReasoner):
        def reason(self, context):
            return ReasoningProposal(
                actions=(
                    ReasoningAction(
                        name="browser_click",
                        description="Click the control.",
                        target="Zatwierdź",
                    ),
                ),
                rationale="Browser context is required.",
                confidence=0.95,
            )

    planner = ReasoningTaskPlanner(BrowserReasoner())

    context = TaskPlanningContext(
        request_message="Kliknij Zatwierdź",
        intent="computer_use",
    )

    assert planner.plan(context=context) is None
    assert planner.last_failure_reason == "browser_context_missing"


def test_browser_click_verification_fails_closed_when_page_does_not_change():
    page = create_page()
    context = create_context(page)
    expected = ExpectationResolver().resolve(
        AgentAction(
            name="browser_click",
            description="Click the submit control.",
            target="Zatwierdź",
        ),
        context,
    )

    assert expected is not None
    assert expected.require_browser_change is True

    result = OutcomeVerifier().verify_browser(
        expected,
        page,
    )

    assert result.verified is False
    assert result.metadata is not None
    assert result.metadata["browser_page_changed"] is False


def test_verification_loop_stops_after_repeated_browser_verification_failure():
    class UnchangedBrowserExecutor:
        def __init__(self, page):
            self.page = page
            self.calls = 0

        def supports(self, action):
            return action.name == "browser_click"

        def execute(self, action, context):
            self.calls += 1
            context.set_value("browser_page", self.page)
            return ExecutionResult(
                action_name=action.name,
                success=True,
                message="Browser click completed.",
                metadata={
                    "browser_operation": "click",
                    "executed": True,
                },
            )

    page = create_page()
    context = create_context(page)
    executor = UnchangedBrowserExecutor(page)

    loop = VerificationLoop(
        execution_engine=ExecutionEngine(
            ExecutorRegistry(
                executors=(executor,),
            )
        ),
        environment=None,
        perception_engine=None,
        expectation_resolver=ExpectationResolver(),
        outcome_verifier=OutcomeVerifier(),
    )

    result = loop.run(
        AgentAction(
            name="browser_click",
            description="Click the submit control.",
            target="Zatwierdź",
        ),
        context,
    )

    assert result.success is False
    assert result.requires_manual_review is True
    assert result.stopped is True
    assert len(result.attempts) == 2
    assert executor.calls == 2
    assert all(
        attempt.verification_result is not None
        and attempt.verification_result.verified is False
        for attempt in result.attempts
    )


def test_browser_dry_run_never_invokes_provider_action():
    adapter, provider = create_adapter(dry_run=True)
    executor = BrowserActionExecutor(adapter)

    result = executor.execute(
        AgentAction(
            name="browser_click",
            description="Dry-run click.",
            target="Zatwierdź",
        ),
        create_context(),
    )

    assert result.success is True
    assert result.metadata is not None
    assert result.metadata["executed"] is False
    assert provider.clicks == []
