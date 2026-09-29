from abc import ABC, abstractmethod

from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.perception.screen_element import ScreenElement


class PerceptionProvider(ABC):
    """
    Produces generic ScreenElement objects from an environment observation.

    The provider may use any perception technology:
    accessibility, OCR, computer vision, browser DOM, etc.
    """

    @abstractmethod
    def perceive(
        self,
        observation: EnvironmentObservation,
    ) -> tuple[ScreenElement, ...]:
        raise NotImplementedError
