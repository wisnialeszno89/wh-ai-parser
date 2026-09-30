from app.agent.agent_action import AgentAction

from app.agent.agent_request import AgentRequest

from app.agent.runtime.execution_context import (
    ExecutionContext,
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
        __import__(
            "app.agent.perception.screen_scene",
            fromlist=["ScreenScene"],
        ).ScreenScene(
            observation=create_context().last_observation
            or __import__(
                "app.agent.environment.environment_observation",
                fromlist=["EnvironmentObservation"],
            ).EnvironmentObservation(
                state=__import__(
                    "app.agent.environment.environment_state",
                    fromlist=["EnvironmentState"],
                ).EnvironmentState(),
            ),
        )
    )

    outcome = resolver.resolve(
        create_action("click_screen_element"),
        context,
    )

    assert outcome is not None
    assert outcome.require_scene_change is True
    assert outcome.baseline_scene_signature == ()
