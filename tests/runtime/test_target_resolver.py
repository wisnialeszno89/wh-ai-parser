from app.agent.agent_request import AgentRequest
from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.target_resolver import TargetResolver


def _scene(*elements):
    observation = EnvironmentObservation(
        state=EnvironmentState(
            active_application="test",
            active_window_title="test",
        )
    )

    return ScreenScene(
        observation=observation,
        elements=tuple(elements),
    )


def test_resolves_exact_label():
    element = ScreenElement(
        kind="button",
        label="TO-0001",
    )

    result = TargetResolver().resolve(
        _scene(element),
        "TO-0001",
    )

    assert result.resolved is True
    assert result.element is element
    assert result.score == 1.0


def test_resolves_semantic_metadata():
    element = ScreenElement(
        kind="icon",
        label="TO-0002",
        metadata={
            "semantic_label": "settings",
        },
    )

    result = TargetResolver().resolve(
        _scene(element),
        "settings",
    )

    assert result.resolved is True
    assert result.element is element
    assert result.score == 0.8


def test_rejects_ambiguous_target():
    first = ScreenElement(
        kind="icon",
        label="TO-0001",
        metadata={"semantic_label": "settings"},
    )

    second = ScreenElement(
        kind="icon",
        label="TO-0002",
        metadata={"semantic_label": "settings"},
    )

    result = TargetResolver().resolve(
        _scene(first, second),
        "settings",
    )

    assert result.resolved is False
    assert result.element is None
    assert "Multiple" in result.reason


def test_rejects_unknown_target():
    element = ScreenElement(
        kind="icon",
        label="TO-0001",
    )

    result = TargetResolver().resolve(
        _scene(element),
        "settings",
    )

    assert result.resolved is False
    assert result.element is None
