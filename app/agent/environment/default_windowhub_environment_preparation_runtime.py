from app.agent.environment.environment_preparation_runtime import (
    EnvironmentPreparationRuntime,
)
from app.agent.environment.environment_preparation_strategy import (
    EnvironmentPreparationStrategy,
)
from app.agent.environment.request_user_action_environment_preparation_handler import (
    RequestUserActionEnvironmentPreparationHandler,
)
from app.agent.environment.unsupported_environment_preparation_strategy_handler import (
    UnsupportedEnvironmentPreparationStrategyHandler,
)
from app.agent.environment.strategy_aware_environment_preparation_executor import (
    StrategyAwareEnvironmentPreparationExecutor,
)
from app.agent.environment.windowhub_focus_window_preparation_handler import (
    WindowHubFocusWindowPreparationHandler,
)


def create_default_windowhub_environment_preparation_runtime(
) -> EnvironmentPreparationRuntime:
    """
    Create WindowHub's concrete environment preparation runtime.

    Focus is implemented locally because LIVE GUI execution requires
    the WindowHub window to own foreground focus.
    """

    executor = StrategyAwareEnvironmentPreparationExecutor(
        handlers=(
            WindowHubFocusWindowPreparationHandler(),
            UnsupportedEnvironmentPreparationStrategyHandler(
                EnvironmentPreparationStrategy.ACTIVATE_APPLICATION
            ),
            UnsupportedEnvironmentPreparationStrategyHandler(
                EnvironmentPreparationStrategy.LAUNCH_APPLICATION
            ),
            RequestUserActionEnvironmentPreparationHandler(),
        )
    )

    return EnvironmentPreparationRuntime(
        executor=executor
    )
