from app.agent.environment.default_environment_preparation_handlers import (
    create_default_environment_preparation_handlers,
)

from app.agent.environment.environment_preparation_runtime import (
    EnvironmentPreparationRuntime,
)

from app.agent.environment.strategy_aware_environment_preparation_executor import (
    StrategyAwareEnvironmentPreparationExecutor,
)


def create_default_environment_preparation_runtime(
) -> EnvironmentPreparationRuntime:
    """
    Create the default safe environment preparation runtime.

    The default runtime only exposes handlers that are safe
    and explicitly supported by the current implementation.

    Unsupported strategies fail safely instead of pretending
    that an environment operation succeeded.
    """

    executor = (
        StrategyAwareEnvironmentPreparationExecutor(
            handlers=(
                create_default_environment_preparation_handlers()
            )
        )
    )

    return EnvironmentPreparationRuntime(
        executor=executor
    )
