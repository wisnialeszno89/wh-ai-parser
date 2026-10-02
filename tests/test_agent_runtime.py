from app.agent.agent_intent import AgentIntent

from types import SimpleNamespace

from app.agent.agent_action import AgentAction
from app.agent.agent_request import AgentRequest
from app.agent.runtime.agent_runtime import AgentRuntime
from app.agent.runtime.execution_context import AgentExecutionContext
from app.agent.planning.action_plan import ActionPlan
from app.agent.planning.action_step import ActionStep
from app.agent.reasoning.reasoning_action import ReasoningAction
from app.agent.reasoning.reasoning_proposal import ReasoningProposal
from app.agent.reasoning.task_reasoner import TaskReasoner

from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.environment.environment_state import (
    EnvironmentState,
)
from app.agent.perception.interaction_capability import (
    InteractionCapability,
)
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene


def test_runtime_requires_manual_review_without_gui_for_quote_request():

    runtime = AgentRuntime()

    result = runtime.run(
        AgentRequest(
            message="Zrób wycenę okna"
        )
    )

    assert result.intent == AgentIntent.CREATE_QUOTE
    assert result.executed is False
    assert result.execution_report is None
    assert result.control_loop_result is None
    assert result.requires_manual_review is True


def test_runtime_requires_manual_review_without_gui_for_incomplete_quote():

    runtime = AgentRuntime()

    result = runtime.run(
        AgentRequest(
            message="Przygotuj ofertę"
        )
    )

    assert result.intent == AgentIntent.CREATE_QUOTE
    assert result.execution_report is None
    assert result.control_loop_result is None
    assert result.executed is False
    assert result.requires_manual_review is True
    assert result.context.get_value("salesperson_questions")


def test_runtime_does_not_execute_legacy_quote_plan_without_gui():

    runtime = AgentRuntime()

    result = runtime.run(
        AgentRequest(
            message="Zrób wycenę okna"
        )
    )

    assert result.intent == AgentIntent.CREATE_QUOTE
    assert result.execution_report is None
    assert result.control_loop_result is None
    assert result.executed is False
    assert result.requires_manual_review is True


def test_runtime_requires_manual_review_for_unknown():

    runtime = AgentRuntime()

    result = runtime.run(
        AgentRequest(
            message=(
                "xyz completely unknown "
                "agent command"
            )
        )
    )

    assert (
        result.intent
        == AgentIntent.UNKNOWN
    )

    assert (
        result.requires_manual_review
        is True
    )

    assert (
        result.executed
        is False
    )

    assert (
        result.execution_report
        is None
    )


class RecordingOrchestrator:
    def __init__(self):
        self.initial_scene = None
        self.context = None

    def prepare(self, request, initial_scene=None):
        self.initial_scene = initial_scene

        action = AgentAction(
            name="click_screen_element",
            description="Open the observed new offer control.",
            target="NOWA OFERTA",
        )

        self.context = AgentExecutionContext(
            request=request,
            intent=AgentIntent.EXECUTE_IN_WH,
            plan=ActionPlan(
                intent=AgentIntent.EXECUTE_IN_WH,
                steps=(
                    ActionStep(
                        index=1,
                        action=action,
                    ),
                ),
                confidence=0.95,
            ),
        )

        return self.context


class RecordingControlLoop:
    def __init__(self, scene):
        self.scene = scene
        self.observation_calls = 0
        self.context = None

    def observe_scene(self):
        self.observation_calls += 1
        return self.scene

    def run(self, plan, context):
        self.context = context
        return SimpleNamespace(
            requires_manual_review=False,
        )


def test_runtime_observes_before_initial_planning():
    scene = ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application="WindowHub",
                active_window_title="WindowHub - Oferta",
            ),
        ),
        elements=(
            ScreenElement(
                kind="button",
                label="NOWA OFERTA",
                confidence=0.99,
                interaction_capability=(
                    InteractionCapability.CLICKABLE
                ),
            ),
        ),
    )

    orchestrator = RecordingOrchestrator()
    control_loop = RecordingControlLoop(scene)

    runtime = AgentRuntime(
        orchestrator=orchestrator,
        control_loop=control_loop,
    )

    result = runtime.run(
        AgentRequest(
            message="Otwórz nową ofertę"
        )
    )

    assert control_loop.observation_calls == 1
    assert orchestrator.initial_scene is scene
    assert control_loop.context is result.context
    assert result.context.current_scene is scene
    assert result.executed is True


class RecordingTaskReasoner(TaskReasoner):
    def __init__(self):
        self.contexts = []

    def reason(self, context):
        self.contexts.append(context)
        return ReasoningProposal(
            actions=(
                ReasoningAction(
                    name="open_new_offer",
                    description="Open the new offer form.",
                    target="NOWA OFERTA",
                ),
            ),
            rationale="Test proposal.",
            confidence=0.8,
        )


def test_runtime_builds_offer_workflow_context_before_task_reasoning():
    reasoner = RecordingTaskReasoner()

    from app.agent.runtime.agent_orchestrator import AgentOrchestrator

    runtime = AgentRuntime(
        orchestrator=AgentOrchestrator(
            task_reasoner=reasoner,
        ),
    )

    runtime.run(
        AgentRequest(
            message="Przygotuj tę ofertę",
        )
    )

    assert len(reasoner.contexts) == 1

    offer_workflow = (
        reasoner.contexts[0].offer_workflow
    )

    assert offer_workflow is not None
    assert "workflow_state" in offer_workflow
    assert "requires_salesperson_input" in offer_workflow
    assert "questions" in offer_workflow
    assert "missing_fields" in offer_workflow
    assert "offer_context" in offer_workflow


def test_runtime_blocks_gui_when_offer_workflow_requires_salesperson_input():
    reasoner = RecordingTaskReasoner()

    from app.agent.runtime.agent_orchestrator import AgentOrchestrator

    runtime = AgentRuntime(
        orchestrator=AgentOrchestrator(
            task_reasoner=reasoner,
        ),
    )

    result = runtime.run(
        AgentRequest(
            message="Przygotuj tę ofertę",
        )
    )

    assert result.executed is False
    assert result.requires_manual_review is True
    assert result.control_loop_result is None
    assert result.context.get_value(
        "salesperson_questions"
    )


def test_runtime_continues_offer_session_with_follow_up_data():
    reasoner = RecordingTaskReasoner()

    from app.agent.runtime.agent_orchestrator import AgentOrchestrator

    runtime = AgentRuntime(
        orchestrator=AgentOrchestrator(
            task_reasoner=reasoner,
        ),
    )

    first = runtime.run(
        AgentRequest(
            message="Przygotuj tę ofertę",
            session_id="offer-session-test",
        )
    )

    assert first.executed is False
    assert first.requires_manual_review is True

    second = runtime.run(
        AgentRequest(
            message="Okno 1230x1480 FIX",
            session_id="offer-session-test",
        )
    )

    assert second.intent == AgentIntent.CREATE_QUOTE
    assert second.executed is True
    assert second.execution_report is not None

    assert len(reasoner.contexts) == 2

    workflow = reasoner.contexts[-1].offer_workflow

    assert workflow is not None
    assert workflow["continuation_of_offer"] is True
    assert workflow["requires_salesperson_input"] is False
    assert workflow["is_ready_for_pricing"] is True
    assert workflow["offer_context"]["width"] == 1230
    assert workflow["offer_context"]["height"] == 1480
    assert workflow["offer_context"]["product_type"] == "window"


class OfferGuiTaskReasoner(TaskReasoner):
    def reason(self, context):
        return ReasoningProposal(
            actions=(
                ReasoningAction(
                    name="click_screen_element",
                    description="Open the new offer dialog.",
                    target="NOWA OFERTA",
                ),
            ),
            rationale="Start the visible WindowHub offer workflow.",
            confidence=0.91,
        )


def test_runtime_allows_gui_reasoning_when_offer_data_can_be_filled():
    scene = ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application="WindowHub",
                active_window_title="WindowHub",
            ),
        ),
        elements=(
            ScreenElement(
                kind="button",
                label="NOWA OFERTA",
                confidence=0.99,
                interaction_capability=(
                    InteractionCapability.CLICKABLE
                ),
            ),
        ),
    )

    from app.agent.runtime.agent_orchestrator import AgentOrchestrator

    runtime = AgentRuntime(
        orchestrator=AgentOrchestrator(
            task_reasoner=OfferGuiTaskReasoner(),
        ),
        control_loop=RecordingControlLoop(scene),
    )

    result = runtime.run(
        AgentRequest(
            message=(
                "Przygotuj nową ofertę. "
                "Okno 1230x1480 FIX."
            ),
            session_id="gui-offer-fill-test",
        )
    )

    assert result.executed is True
    assert result.requires_manual_review is False
    assert result.control_loop_result is not None
    assert result.context.plan.steps[0].action.name == (
        "click_screen_element"
    )
