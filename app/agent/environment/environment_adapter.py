from abc import ABC, abstractmethod

from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)


class EnvironmentAdapter(ABC):
    """
    Platform-specific adapter used to observe the external
    environment.

    The agent runtime depends only on this interface.

    Implementations may later represent:
    - fake environments
    - Windows desktop
    - browsers
    - WH
    - remote environments
    """

    @abstractmethod
    def observe(
        self,
    ) -> EnvironmentObservation:
        """
        Return the current environment observation.
        """
        raise NotImplementedError
