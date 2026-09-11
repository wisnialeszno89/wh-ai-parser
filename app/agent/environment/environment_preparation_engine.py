from app.agent.environment.environment_preparation import (
    EnvironmentPreparation,
)

from app.agent.environment.environment_preparation_strategy import (
    EnvironmentPreparationStrategy,
)

from app.agent.environment.environment_preparation_type import (
    EnvironmentPreparationType,
)

from app.agent.environment.environment_readiness_result import (
    EnvironmentReadinessResult,
)

from app.agent.environment.environment_requirement import (
    EnvironmentRequirement,
)


class EnvironmentPreparationEngine:
    """
    Determines how the agent should react when the current
    environment is or is not ready.

    The engine decides:

    - whether preparation is required
    - what semantic preparation should happen
    - which preparation strategy should be used

    The engine intentionally remains independent from:

    - Windows APIs
    - browser automation
    - WH
    - GUI clicking

    It only produces a semantic preparation decision.
    """

    def prepare(
        self,
        requirement: EnvironmentRequirement,
        result: EnvironmentReadinessResult,
    ) -> EnvironmentPreparation:
        """
        Decide what should happen before execution may begin.
        """

        if result.is_ready:
            return EnvironmentPreparation(
                preparation_type=(
                    EnvironmentPreparationType.READY
                ),
                strategy=(
                    EnvironmentPreparationStrategy.NONE
                ),
                target_application=(
                    requirement.application
                ),
                reason=(
                    "Environment is ready for execution."
                ),
            )

        if result.requires_manual_intervention:
            return EnvironmentPreparation(
                preparation_type=(
                    EnvironmentPreparationType
                    .USER_ACTION_REQUIRED
                ),
                strategy=(
                    EnvironmentPreparationStrategy
                    .REQUEST_USER_ACTION
                ),
                target_application=(
                    result.target_application
                    or requirement.application
                ),
                reason=result.reason,
                instructions=(
                    "Prepare the required environment "
                    "and try again.",
                ),
            )

        if requirement.application is not None:
            return EnvironmentPreparation(
                preparation_type=(
                    EnvironmentPreparationType.PREPARE
                ),
                strategy=(
                    EnvironmentPreparationStrategy
                    .ACTIVATE_APPLICATION
                ),
                target_application=(
                    requirement.application
                ),
                reason=(
                    result.reason
                    or
                    "Required application is not active."
                ),
                instructions=(
                    "Activate the required application.",
                ),
            )

        if (
            requirement.window_title is not None
            or requirement.requires_focus
        ):
            return EnvironmentPreparation(
                preparation_type=(
                    EnvironmentPreparationType.PREPARE
                ),
                strategy=(
                    EnvironmentPreparationStrategy
                    .FOCUS_WINDOW
                ),
                target_application=(
                    result.target_application
                ),
                reason=(
                    result.reason
                    or
                    "Required window does not have focus."
                ),
                instructions=(
                    "Focus the required window.",
                ),
            )

        return EnvironmentPreparation(
            preparation_type=(
                EnvironmentPreparationType
                .USER_ACTION_REQUIRED
            ),
            strategy=(
                EnvironmentPreparationStrategy
                .REQUEST_USER_ACTION
            ),
            reason=(
                result.reason
                or
                "Environment is not ready and no "
                "automatic preparation strategy "
                "is available."
            ),
            instructions=(
                "Prepare the required environment "
                "and try again.",
            ),
        )
