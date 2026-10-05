from app.agent.agent_request import AgentRequest
from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.environment.environment_readiness import (
    EnvironmentReadiness,
)
from app.agent.environment.environment_readiness_evaluator import (
    EnvironmentReadinessEvaluator,
)
from app.agent.environment.environment_requirement import (
    EnvironmentRequirement,
)
from app.agent.environment.environment_state import (
    EnvironmentState,
)
from app.agent.planning.agent_planner import AgentPlanner


def _observation(focused: bool) -> EnvironmentObservation:
    return EnvironmentObservation(
        state=EnvironmentState(
            active_application="WindowHub",
            active_window_title="Okna - TEST",
            screen_width=100,
            screen_height=100,
        ),
        metadata={
            "window_focused": focused,
        },
    )


def test_focus_requirement_is_not_ready_without_focus():
    requirement = EnvironmentRequirement(
        application="WindowHub",
        requires_focus=True,
    )

    result = EnvironmentReadinessEvaluator().evaluate(
        requirement,
        _observation(False),
    )

    assert result.readiness is EnvironmentReadiness.PREPARATION_REQUIRED


def test_focus_requirement_is_ready_with_focus():
    requirement = EnvironmentRequirement(
        application="WindowHub",
        requires_focus=True,
    )

    result = EnvironmentReadinessEvaluator().evaluate(
        requirement,
        _observation(True),
    )

    assert result.readiness is EnvironmentReadiness.READY


def test_windowhub_click_plan_requires_focus():
    plan = AgentPlanner().plan(
        AgentRequest(message="Kliknij NOWA OFERTA")
    )

    assert len(plan.steps) == 1

    requirement = plan.steps[0].action.environment_requirement

    assert requirement is not None
    assert requirement.application == "WindowHub"
    assert requirement.requires_focus is True
