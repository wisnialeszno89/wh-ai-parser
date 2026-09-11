from app.agent.environment.default_environment_preparation_runtime import (
    create_default_environment_preparation_runtime,
)

from app.agent.environment.environment_adapter import (
    EnvironmentAdapter,
)

from app.agent.environment.environment_preparation_engine import (
    EnvironmentPreparationEngine,
)

from app.agent.environment.environment_preparation_loop import (
    EnvironmentPreparationLoop,
)

from app.agent.environment.environment_readiness_evaluator import (
    EnvironmentReadinessEvaluator,
)


def create_default_environment_preparation_loop(
    *,
    environment: EnvironmentAdapter,
) -> EnvironmentPreparationLoop:
    """
    Create a complete default environment preparation loop.

    This factory provides the standard safe runtime used by
    agent components that do not require a platform-specific
    environment implementation.

    Platform-specific factories may later provide:

    - Windows environment preparation
    - browser environment preparation
    - simulator environment preparation
    """

    return EnvironmentPreparationLoop(
        environment=environment,
        readiness_evaluator=(
            EnvironmentReadinessEvaluator()
        ),
        preparation_engine=(
            EnvironmentPreparationEngine()
        ),
        preparation_executor=(
            create_default_environment_preparation_runtime()
        ),
    )
