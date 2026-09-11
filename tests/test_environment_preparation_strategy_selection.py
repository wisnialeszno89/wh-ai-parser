from app.agent.environment.environment_preparation_engine import (
    EnvironmentPreparationEngine,
)

from app.agent.environment.environment_preparation_strategy import (
    EnvironmentPreparationStrategy,
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


def test_ready_environment_uses_none_strategy():

    engine = EnvironmentPreparationEngine()

    requirement = EnvironmentRequirement(
        application="WindowHelper"
    )

    result = EnvironmentReadinessResult(
        readiness=EnvironmentReadiness.READY
    )

    preparation = engine.prepare(
        requirement,
        result,
    )

    assert (
        preparation.strategy
        == EnvironmentPreparationStrategy.NONE
    )

    assert (
        preparation.preparation_type
        == EnvironmentPreparationType.READY
    )


def test_missing_application_uses_activate_strategy():

    engine = EnvironmentPreparationEngine()

    requirement = EnvironmentRequirement(
        application="WindowHelper"
    )

    result = EnvironmentReadinessResult(
        readiness=(
            EnvironmentReadiness
            .PREPARATION_REQUIRED
        ),
        reason=(
            "Required application is not active."
        ),
        target_application="WindowHelper",
    )

    preparation = engine.prepare(
        requirement,
        result,
    )

    assert (
        preparation.strategy
        == EnvironmentPreparationStrategy
        .ACTIVATE_APPLICATION
    )

    assert (
        preparation.target_application
        == "WindowHelper"
    )


def test_window_requirement_uses_focus_strategy():

    engine = EnvironmentPreparationEngine()

    requirement = EnvironmentRequirement(
        window_title="WindowHelper Quote",
        requires_focus=True,
    )

    result = EnvironmentReadinessResult(
        readiness=(
            EnvironmentReadiness
            .PREPARATION_REQUIRED
        ),
        reason=(
            "Required window is not focused."
        ),
    )

    preparation = engine.prepare(
        requirement,
        result,
    )

    assert (
        preparation.strategy
        == EnvironmentPreparationStrategy
        .FOCUS_WINDOW
    )

    assert (
        preparation.preparation_type
        == EnvironmentPreparationType.PREPARE
    )


def test_manual_intervention_requests_user_action():

    engine = EnvironmentPreparationEngine()

    requirement = EnvironmentRequirement(
        application="WindowHelper"
    )

    result = EnvironmentReadinessResult(
        readiness=(
            EnvironmentReadiness
            .MANUAL_INTERVENTION_REQUIRED
        ),
        reason="User login is required.",
        requires_manual_intervention=True,
    )

    preparation = engine.prepare(
        requirement,
        result,
    )

    assert (
        preparation.strategy
        == EnvironmentPreparationStrategy
        .REQUEST_USER_ACTION
    )

    assert (
        preparation.preparation_type
        == EnvironmentPreparationType
        .USER_ACTION_REQUIRED
    )


def test_unknown_requirement_requests_user_action():

    engine = EnvironmentPreparationEngine()

    requirement = EnvironmentRequirement()

    result = EnvironmentReadinessResult(
        readiness=(
            EnvironmentReadiness
            .PREPARATION_REQUIRED
        ),
        reason="Environment is not ready.",
    )

    preparation = engine.prepare(
        requirement,
        result,
    )

    assert (
        preparation.strategy
        == EnvironmentPreparationStrategy
        .REQUEST_USER_ACTION
    )
