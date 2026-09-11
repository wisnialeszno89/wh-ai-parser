from app.agent.agent_action import AgentAction
from app.agent.agent_request import AgentRequest

from app.agent.decision.decision_engine import (
    DecisionEngine,
)

from app.agent.decision.decision_type import (
    DecisionType,
)

from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)

from app.agent.environment.environment_state import (
    EnvironmentState,
)

from app.agent.perception.screen_element import (
    ScreenElement,
)

from app.agent.perception.screen_scene import (
    ScreenScene,
)

from app.agent.runtime.execution_context import (
    ExecutionContext,
)


def create_context() -> ExecutionContext:

    return ExecutionContext(
        request=AgentRequest(
            message="Test request"
        )
    )


def create_action() -> AgentAction:

    return AgentAction(
        name="test_action",
        description="Test action",
    )


def create_observation() -> EnvironmentObservation:

    return EnvironmentObservation(
        state=EnvironmentState()
    )


def test_decision_engine_proceeds_when_no_blocker():

    engine = DecisionEngine()

    context = create_context()

    decision = engine.decide(
        create_action(),
        context,
    )

    assert (
        decision.decision_type
        == DecisionType.PROCEED
    )

    assert (
        decision.requires_manual_review
        is False
    )


def test_decision_engine_requires_review_when_context_requires_review():

    engine = DecisionEngine()

    context = create_context()

    context.requires_manual_review = True

    decision = engine.decide(
        create_action(),
        context,
    )

    assert (
        decision.decision_type
        == DecisionType.MANUAL_REVIEW
    )

    assert (
        decision.requires_manual_review
        is True
    )


def test_decision_engine_requires_review_for_dialog():

    engine = DecisionEngine()

    context = create_context()

    context.current_scene = ScreenScene(
        observation=create_observation(),
        elements=(
            ScreenElement(
                kind="dialog",
                label="Save changes?"
            ),
        ),
    )

    decision = engine.decide(
        create_action(),
        context,
    )

    assert (
        decision.decision_type
        == DecisionType.MANUAL_REVIEW
    )

    assert (
        decision.target
        == "Save changes?"
    )

    assert (
        decision.requires_manual_review
        is True
    )


def test_decision_engine_proceeds_for_normal_scene():

    engine = DecisionEngine()

    context = create_context()

    context.current_scene = ScreenScene(
        observation=create_observation(),
        elements=(
            ScreenElement(
                kind="button",
                label="New Project"
            ),
        ),
    )

    decision = engine.decide(
        create_action(),
        context,
    )

    assert (
        decision.decision_type
        == DecisionType.PROCEED
    )
