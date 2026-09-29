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

    Perception providers supply ScreenElement objects independently
    of the technology used to detect them.
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

        elements: list = []

        for provider in self.providers:
            elements.extend(
                provider.perceive(observation)
            )

        scene_metadata = dict(observation.metadata)
        scene_metadata["provider_count"] = len(self.providers)

        return ScreenScene(
            observation=observation,
            elements=tuple(elements),
            metadata=scene_metadata,
        )
