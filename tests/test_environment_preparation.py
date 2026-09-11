from app.agent.environment.environment_preparation_engine import (
    EnvironmentPreparationEngine,
)

from app.agent.environment.environment_preparation_type import (
    EnvironmentPreparationType,
)

from app.agent.environment.environment_readiness import (
    EnvironmentReadiness,
)

from app.agent.environment.environment_readiness_result import (
    EnvironmentReadinessResult,
)

from app.agent.environment.environment_requirement import (
    EnvironmentRequirement,
)


def create_requirement():

    return EnvironmentRequirement(
        application="WindowHelper"
    )


def create_ready_result():

    return EnvironmentReadinessResult(
        readiness=EnvironmentReadiness.READY,
        reason="Environment ready.",
        target_application="WindowHelper",
    )


def create_not_ready_result():

    return EnvironmentReadinessResult(
        readiness=(
            EnvironmentReadiness.PREPARATION_REQUIRED
        ),
        reason=(
            "Required application is not active."
        ),
        target_application="WindowHelper",
    )


def test_preparation_reports_ready_environment():

    engine = EnvironmentPreparationEngine()

    preparation = engine.prepare(
        create_requirement(),
        create_ready_result(),
    )

    assert (
        preparation.preparation_type
        == EnvironmentPreparationType.READY
    )

    assert (
        preparation.target_application
        == "WindowHelper"
    )


def test_preparation_requests_required_application():

    engine = EnvironmentPreparationEngine()

    preparation = engine.prepare(
        create_requirement(),
        create_not_ready_result(),
    )

    assert (
        preparation.preparation_type
        == EnvironmentPreparationType.PREPARE
    )

    assert (
        preparation.target_application
        == "WindowHelper"
    )

    assert (
        preparation.instructions
        == (
            "Activate the required application.",
        )
    )


def test_preparation_requires_user_action_without_target():

    engine = EnvironmentPreparationEngine()

    requirement = EnvironmentRequirement()

    preparation = engine.prepare(
        requirement,
        create_not_ready_result(),
    )

    assert (
        preparation.preparation_type
        == EnvironmentPreparationType.USER_ACTION_REQUIRED
    )

    assert (
        preparation.requires_user_action
        is True
    )


def test_preparation_ready_does_not_require_user_action():

    engine = EnvironmentPreparationEngine()

    preparation = engine.prepare(
        create_requirement(),
        create_ready_result(),
    )

    assert (
        preparation.requires_user_action
        is False
    )

    assert (
        preparation.requires_manual_review
        is False
    )

    assert (
        preparation.should_stop
        is False
    )
