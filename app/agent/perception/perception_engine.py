from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)

from app.agent.perception.perception_provider import (
    PerceptionProvider,
)

from app.agent.perception.screen_scene import (
    ScreenScene,
)


class PerceptionEngine:
    """
    Converts environment observations into semantic scenes.

    Concrete providers may enrich the scene through:
    - accessibility APIs
    - browser DOM
    - OCR
    - computer vision
    - template matching

    The engine is deliberately provider-driven so the Universal
    Agent Core remains independent from any single environment.
    """

    def __init__(
        self,
        providers: tuple[PerceptionProvider, ...] = (),
    ) -> None:
        self.providers = providers

    def perceive(
        self,
        observation: EnvironmentObservation,
    ) -> ScreenScene:

        elements = []

        for provider in self.providers:
            elements.extend(
                provider.perceive(observation)
            )

        return ScreenScene(
            observation=observation,
            elements=tuple(elements),
            metadata={
                "provider_count": len(self.providers),
            },
        )
