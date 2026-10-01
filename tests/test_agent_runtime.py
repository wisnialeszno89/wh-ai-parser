from app.agent.agent_intent import AgentIntent

from types import SimpleNamespace

from app.agent.agent_action import AgentAction
from app.agent.agent_request import AgentRequest
from app.agent.runtime.agent_runtime import AgentRuntime
from app.agent.runtime.execution_context import AgentExecutionContext
from app.agent.planning.action_plan import ActionPlan
from app.agent.planning.action_step import ActionStep

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


def test_runtime_executes_quote_request():

    runtime = AgentRuntime()

    result = runtime.run(
        AgentRequest(
            message="Zrób wycenę okna"
        )
    )

    assert (
        result.intent
        == AgentIntent.CREATE_QUOTE
    )

    assert result.executed is True

    assert (
        result.execution_report
        is not None
    )


def test_runtime_returns_execution_report():

    runtime = AgentRuntime()

    result = runtime.run(
        AgentRequest(
            message="Przygotuj ofertę"
        )
    )

    assert (
        result.execution_report
        is not None
    )

    assert (
        len(
            result.execution_report.results
        )
        > 0
    )


def test_runtime_executes_wh_plan():

    runtime = AgentRuntime()

    result = runtime.run(
        AgentRequest(
            message="Zrób wycenę okna"
        )
    )

    names = [
        item.action_name
        for item in (
            result.execution_report.results
        )
    ]

    assert (
        "analyze_request"
        in names
    )

    assert (
        "collect_offer_context"
        in names
    )

    assert (
        "validate_offer"
        in names
    )

    assert (
        "build_construction"
        not in names
    )

    assert (
        "prepare_quote"
        not in names
    )

    assert result.requires_manual_review is True

    validation_result = next(
        item
        for item in result.execution_report.results
        if item.action_name == "validate_offer"
    )

    assert validation_result.success is False

    assert validation_result.requires_manual_review is True

    assert validation_result.metadata is not None

    assert "width" in validation_result.metadata["missing_fields"]

    assert "height" in validation_result.metadata["missing_fields"]


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
