from app.agent.environment.environment_observation import (
    EnvironmentObservation,
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


class EnvironmentReadinessEvaluator:
    """
    Evaluates whether an observed environment satisfies
    the requirements needed to continue execution.

    This layer only evaluates readiness.

    It does not:
    - activate windows
    - launch applications
    - interact with the operating system

    Those responsibilities will belong to the future
    environment preparation layer.
    """

    def evaluate(
        self,
        requirement: EnvironmentRequirement,
        observation: EnvironmentObservation,
    ) -> EnvironmentReadinessResult:

        state = observation.state

        if (
            requirement.application is not None
            and state.active_application is None
        ):
            return EnvironmentReadinessResult(
                readiness=(
                    EnvironmentReadiness.MANUAL_INTERVENTION_REQUIRED
                ),
                reason=(
                    "No active application is available "
                    "to satisfy the environment requirement."
                ),
                target_application=(
                    requirement.application
                ),
                target_window_title=(
                    requirement.window_title
                ),
                requires_manual_intervention=True,
            )

        if (
            requirement.application is not None
            and state.active_application.casefold()
            != requirement.application.casefold()
        ):
            return EnvironmentReadinessResult(
                readiness=(
                    EnvironmentReadiness.PREPARATION_REQUIRED
                ),
                reason=(
                    "Required application is not active."
                ),
                target_application=(
                    requirement.application
                ),
                target_window_title=(
                    requirement.window_title
                ),
            )

        if (
            requirement.window_title is not None
            and state.active_window_title is None
        ):
            return EnvironmentReadinessResult(
                readiness=(
                    EnvironmentReadiness.PREPARATION_REQUIRED
                ),
                reason=(
                    "Required window title is not available."
                ),
                target_application=(
                    requirement.application
                ),
                target_window_title=(
                    requirement.window_title
                ),
            )

        if (
            requirement.window_title is not None
            and requirement.window_title.casefold()
            not in state.active_window_title.casefold()
        ):
            return EnvironmentReadinessResult(
                readiness=(
                    EnvironmentReadiness.PREPARATION_REQUIRED
                ),
                reason=(
                    "Active window does not satisfy "
                    "the environment requirement."
                ),
                target_application=(
                    requirement.application
                ),
                target_window_title=(
                    requirement.window_title
                ),
            )

        return EnvironmentReadinessResult(
            readiness=EnvironmentReadiness.READY,
            reason=(
                "Environment satisfies the current "
                "requirements."
            ),
            target_application=(
                requirement.application
            ),
            target_window_title=(
                requirement.window_title
            ),
        )
