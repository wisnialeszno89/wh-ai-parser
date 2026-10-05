from app.agent.environment.default_windowhub_environment_preparation_runtime import (
    create_default_windowhub_environment_preparation_runtime,
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


def create_default_windowhub_environment_preparation_loop(
    *,
    environment: EnvironmentAdapter,
) -> EnvironmentPreparationLoop:
    """
    Create the WindowHub-specific environment preparation loop.

    It keeps the generic readiness/strategy layers while supplying the
    concrete WindowHub focus runtime.
    """

    return EnvironmentPreparationLoop(
        environment=environment,
        readiness_evaluator=EnvironmentReadinessEvaluator(),
        preparation_engine=EnvironmentPreparationEngine(),
        preparation_executor=(
            create_default_windowhub_environment_preparation_runtime()
        ),
    )
