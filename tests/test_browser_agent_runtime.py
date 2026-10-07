from dataclasses import dataclass

from app.agent.adapters.browser_adapter import (
    BrowserAdapter,
    BrowserElement,
    BrowserPage,
)
from app.agent.agent_intent import AgentIntent
from app.agent.agent_request import AgentRequest
from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.environment.environment_state import (
    EnvironmentState,
)
from app.agent.perception.screen_scene import ScreenScene
from app.agent.reasoning.navimind_task_reasoner import (
    NaviMindTaskReasonerConfig,
)
from app.agent.reasoning.reasoning_action import ReasoningAction
from app.agent.reasoning.reasoning_proposal import ReasoningProposal
from app.agent.reasoning.task_reasoner import TaskReasoner
from app.agent.runtime.agent_orchestrator import AgentOrchestrator
from app.agent.runtime.agent_runtime import AgentRuntime


@dataclass
class FakeBrowserProvider:
    page: BrowserPage
    available: bool = True

    def is_available(self):
        return self.available

    def current_page(self):
        return self.page

    def open(self, url):
        return self.page

    def click(self, target):
        return self.page

    def write_text(self, target, value):
        return self.page

    def select_option(self, target, value):
        return self.page

    def back(self):
        return self.page


class RecordingTaskReasoner(TaskReasoner):
    def __init__(self):
        self.contexts = []

    def reason(self, context):
        self.contexts.append(context)
        return ReasoningProposal(
            actions=(
                ReasoningAction(
                    name="browser_click",
                    description="Click the visible next control.",
                    target="Dalej",
                ),
            ),
            rationale="Advance the browser workflow.",
            confidence=0.96,
        )


class RecordingControlLoop:
    def __init__(self):
        self.context = None

    def observe_scene(self):
        return ScreenScene(
            observation=EnvironmentObservation(
                state=EnvironmentState(
                    active_application="Browser",
                    active_window_title="Example Form",
                ),
            )
        )

    def run(self, plan, context):
        self.context = context

        return type(
            "ControlResult",
            (),
            {
                "requires_manual_review": False,
            },
        )()


def create_browser_adapter():
    page = BrowserPage(
        url="https://example.com/form",
        title="Example Form",
        text="Formularz klienta",
        elements=(
            BrowserElement(
                label="Dalej",
                kind="button",
                interaction_capability="CLICKABLE",
                confidence=0.99,
            ),
        ),
    )

    return BrowserAdapter(
        provider=FakeBrowserProvider(page),
        allowed_domains=("example.com",),
        dry_run=True,
    )


def test_runtime_passes_live_browser_page_into_navimind_context():
    reasoner = RecordingTaskReasoner()
    control_loop = RecordingControlLoop()

    runtime = AgentRuntime(
        orchestrator=AgentOrchestrator(
            task_reasoner=reasoner,
            require_task_reasoning=True,
        ),
        control_loop=control_loop,
        browser_adapter=create_browser_adapter(),
        browser_context_enabled=True,
    )

    result = runtime.run(
        AgentRequest(
            message="Przejdź dalej w formularzu",
            metadata={
                "target_application": "Browser",
            },
        )
    )

    assert result.intent == AgentIntent.COMPUTER_USE
    assert result.executed is True
    assert result.requires_manual_review is False

    assert len(reasoner.contexts) == 1
    context = reasoner.contexts[0]

    assert context.browser_page is not None
    assert context.browser_page.url == "https://example.com/form"
    assert context.world is not None
    assert context.world.application is None
    assert context.world.to_payload() == (
        {
            "application": None,
            "window_title": None,
            "active_document": None,
            "entities": [],
            "affordances": [],
            "metadata": {},
        }
        if context.world
        else None
    ) is False

    assert context.browser_page.elements[0].label == "Dalej"
    assert context.world is None or "Dalej" in str(
        context.browser_page.elements
    )
    assert result.context.plan is not None
    assert result.context.plan.steps[0].action.name == "browser_click"
