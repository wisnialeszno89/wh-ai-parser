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


def create_observation(
    *,
    application="WH",
    window_title="WH Main Window",
):

    return EnvironmentObservation(
        state=EnvironmentState(
            active_application=application,
            active_window_title=window_title,
            screen_width=1920,
            screen_height=1080,
        )
    )


def test_environment_is_ready_when_requirement_matches():

    evaluator = EnvironmentReadinessEvaluator()

    result = evaluator.evaluate(
        EnvironmentRequirement(
            application="WH",
            window_title="WH",
        ),
        create_observation(),
    )

    assert (
        result.readiness
        == EnvironmentReadiness.READY
    )

    assert result.is_ready is True


def test_environment_requires_preparation_when_application_differs():

    evaluator = EnvironmentReadinessEvaluator()

    result = evaluator.evaluate(
        EnvironmentRequirement(
            application="WH",
        ),
        create_observation(
            application="Chrome"
        ),
    )

    assert (
        result.readiness
        == EnvironmentReadiness.PREPARATION_REQUIRED
    )

    assert result.is_ready is False

    assert (
        result.target_application
        == "WH"
    )


def test_environment_requires_preparation_when_window_differs():

    evaluator = EnvironmentReadinessEvaluator()

    result = evaluator.evaluate(
        EnvironmentRequirement(
            application="WH",
            window_title="Customer",
        ),
        create_observation(
            window_title="WH Main Window"
        ),
    )

    assert (
        result.readiness
        == EnvironmentReadiness.PREPARATION_REQUIRED
    )


def test_environment_requires_manual_intervention_without_active_application():

    evaluator = EnvironmentReadinessEvaluator()

    result = evaluator.evaluate(
        EnvironmentRequirement(
            application="WH",
        ),
        create_observation(
            application=None
        ),
    )

    assert (
        result.readiness
        == (
            EnvironmentReadiness
            .MANUAL_INTERVENTION_REQUIRED
        )
    )

    assert (
        result.requires_manual_intervention
        is True
    )


def test_environment_without_requirements_is_ready():

    evaluator = EnvironmentReadinessEvaluator()

    result = evaluator.evaluate(
        EnvironmentRequirement(),
        create_observation(
            application="Chrome"
        ),
    )

    assert (
        result.readiness
        == EnvironmentReadiness.READY
    )
