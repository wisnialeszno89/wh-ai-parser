from abc import ABC, abstractmethod

from app.agent.environment.environment_preparation import (
    EnvironmentPreparation,
)

from app.agent.environment.environment_preparation_result import (
    EnvironmentPreparationResult,
)


class EnvironmentPreparationExecutor(ABC):
    """
    Executes environment preparation operations.

    The preparation engine decides WHAT should happen.

    The executor performs the platform-specific operation
    required to achieve that state.

    Implementations may later support:

    - Windows application activation
    - browser activation
    - window focus
    - application startup
    - remote environments
    """

    @abstractmethod
    def execute(
        self,
        preparation: EnvironmentPreparation,
    ) -> EnvironmentPreparationResult:
        """
        Execute the requested environment preparation.
        """

        raise NotImplementedError
