from abc import ABC, abstractmethod

from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)

from app.agent.perception.screen_element import (
    ScreenElement,
)


class PerceptionProvider(ABC):
    """
    Provider of semantic screen elements.

    Providers adapt environment-specific perception systems
    (accessibility, browser DOM, OCR, computer vision, etc.)
    into the Universal Agent Core screen model.
    """

    @abstractmethod
    def perceive(
        self,
        observation: EnvironmentObservation,
    ) -> tuple[ScreenElement, ...]:
        raise NotImplementedError
