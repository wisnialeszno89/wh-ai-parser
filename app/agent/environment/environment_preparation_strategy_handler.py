from abc import ABC, abstractmethod

from app.agent.environment.environment_preparation import (
    EnvironmentPreparation,
)

from app.agent.environment.environment_preparation_result import (
    EnvironmentPreparationResult,
)

from app.agent.environment.environment_preparation_strategy import (
    EnvironmentPreparationStrategy,
)


class EnvironmentPreparationStrategyHandler(ABC):
    """
    Handles one semantic environment preparation strategy.

    Implementations perform the concrete platform-specific
    operation required by a strategy.
    """

    @property
    @abstractmethod
    def strategy(
        self,
    ) -> EnvironmentPreparationStrategy:
        """
        Strategy handled by this implementation.
        """

        raise NotImplementedError

    @abstractmethod
    def execute(
        self,
        preparation: EnvironmentPreparation,
    ) -> EnvironmentPreparationResult:
        """
        Execute the preparation using this strategy.
        """

        raise NotImplementedError
