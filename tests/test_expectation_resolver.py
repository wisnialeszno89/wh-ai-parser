from app.agent.agent_action import AgentAction

from app.agent.agent_request import AgentRequest

from app.agent.runtime.execution_context import (
    ExecutionContext,
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

from app.agent.verification.expected_outcome import (
    ExpectedOutcome,
)

from app.agent.verification.expectation_resolver import (
    ExpectationResolver,
)


def create_action(
    name="test_action",
):

    return AgentAction(
        name=name,
        description="Test action",
    )


def create_context():

    return ExecutionContext(
        request=AgentRequest(
            message="Test request"
        )
    )


def test_resolver_returns_none_without_expectation():

    resolver = ExpectationResolver()

    outcome = resolver.resolve(
        create_action(),
        create_context(),
    )

    assert outcome is None


def test_resolver_returns_context_expectation():

    resolver = ExpectationResolver()

    context = create_context()

    expected = ExpectedOutcome(
        description=(
            "Save dialog should disappear."
        ),
        expected_element_label=(
            "Save changes?"
        ),
        element_should_exist=False,
    )

    context.set_value(
        "expected_outcomes",
        {
            "test_action": expected,
        },
    )

    outcome = resolver.resolve(
        create_action(),
        context,
    )

    assert outcome == expected


def test_resolver_ignores_invalid_context_expectation():

    resolver = ExpectationResolver()

    context = create_context()

    context.set_value(
        "expected_outcomes",
        {
            "test_action": (
                "not an expected outcome"
            ),
        },
    )

    outcome = resolver.resolve(
        create_action(),
        context,
    )

    assert outcome is None


def test_resolver_ignores_invalid_expectation_container():

    resolver = ExpectationResolver()

    context = create_context()

    context.set_value(
        "expected_outcomes",
        "invalid",
    )

    outcome = resolver.resolve(
        create_action(),
        context,
    )

    assert outcome is None


def test_resolver_adds_safe_default_for_gui_click():

    resolver = ExpectationResolver()
    context = create_context()

    context.update_scene(
        ScreenScene(
            observation=EnvironmentObservation(
                state=EnvironmentState()
            )
        )
    )

    outcome = resolver.resolve(
        create_action("click_screen_element"),
        context,
    )

    assert outcome is not None
    assert outcome.require_scene_change is True
    assert outcome.baseline_scene_signature == ()


def test_resolver_adds_value_expectation_for_write_text():

    resolver = ExpectationResolver()
    context = create_context()

    target = ScreenElement(
        kind="edit",
        label="Szerokość",
        x=0,
        y=0,
        width=100,
        height=30,
        confidence=0.99,
        metadata={
            "semantic_name": "Szerokość",
            "current_value": "1000",
        },
    )

    context.update_scene(
        ScreenScene(
            observation=EnvironmentObservation(
                state=EnvironmentState()
            ),
            elements=(target,),
        )
    )

    outcome = resolver.resolve(
        AgentAction(
            name="write_text",
            description="Wpisz szerokość",
            target="Szerokość",
            value="1230",
        ),
        context,
    )

    assert outcome is not None
    assert outcome.expected_element_label == "Szerokość"
    assert outcome.expected_element_current_value == "1230"


def test_target_resolver_supports_semantic_name():

    from app.agent.perception.target_resolver import TargetResolver

    target = ScreenElement(
        kind="edit",
        label=None,
        x=0,
        y=0,
        width=100,
        height=30,
        confidence=0.99,
        metadata={
            "semantic_name": "Wysokość",
        },
    )

    resolution = TargetResolver().resolve(
        ScreenScene(
            observation=EnvironmentObservation(
                state=EnvironmentState()
            ),
            elements=(target,),
        ),
        "Wysokość",
    )

    assert resolution.resolved is True
    assert resolution.element is target
    assert resolution.score == 0.8
