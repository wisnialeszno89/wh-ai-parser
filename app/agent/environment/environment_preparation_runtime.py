from app.agent.environment.environment_preparation import (
    EnvironmentPreparation,
)

from app.agent.environment.environment_preparation_executor import (
    EnvironmentPreparationExecutor,
)

from app.agent.environment.environment_preparation_result import (
    EnvironmentPreparationResult,
)


class EnvironmentPreparationRuntime(
    EnvironmentPreparationExecutor
):
    """
    Runtime wrapper responsible for executing environment
    preparation operations.

    The runtime hides the concrete strategy executor from
    higher-level agent components.

    Future runtime implementations may provide different
    capability sets, for example:

    - safe/default runtime
    - Windows runtime
    - browser runtime
    - simulator runtime
    """

    def __init__(
        self,
        executor: EnvironmentPreparationExecutor,
    ) -> None:

        self._executor = executor

    def execute(
        self,
        preparation: EnvironmentPreparation,
    ) -> EnvironmentPreparationResult:
        """
        Execute the supplied environment preparation through
        the configured runtime executor.
        """

        return self._executor.execute(
            preparation
        )
