from app.agent.environment.environment_preparation_strategy import (
    EnvironmentPreparationStrategy,
)

from app.agent.environment.environment_preparation_strategy_handler import (
    EnvironmentPreparationStrategyHandler,
)

from app.agent.environment.request_user_action_environment_preparation_handler import (
    RequestUserActionEnvironmentPreparationHandler,
)

from app.agent.environment.unsupported_environment_preparation_strategy_handler import (
    UnsupportedEnvironmentPreparationStrategyHandler,
)


def create_default_environment_preparation_handlers(
) -> tuple[
    EnvironmentPreparationStrategyHandler,
    ...,
]:
    """
    Create the default safe environment preparation handlers.

    Platform-specific runtimes may replace these handlers with
    concrete Windows, browser or remote implementations.
    """

    return (
        UnsupportedEnvironmentPreparationStrategyHandler(
            EnvironmentPreparationStrategy
            .ACTIVATE_APPLICATION
        ),
        UnsupportedEnvironmentPreparationStrategyHandler(
            EnvironmentPreparationStrategy
            .FOCUS_WINDOW
        ),
        UnsupportedEnvironmentPreparationStrategyHandler(
            EnvironmentPreparationStrategy
            .LAUNCH_APPLICATION
        ),
        RequestUserActionEnvironmentPreparationHandler(),
    )
