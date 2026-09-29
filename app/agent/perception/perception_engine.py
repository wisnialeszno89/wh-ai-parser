from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)

from app.agent.perception.perception_provider import (
    PerceptionProvider,
)

from app.agent.perception.screen_element_fusion import (
    ScreenElementFusion,
)

from app.agent.perception.screen_scene import (
    ScreenScene,
)


class PerceptionEngine:
    """
    Converts environment observations into semantic scenes.

    Perception providers supply ScreenElement objects independently
    of the technology used to detect them.

    Provider outputs are fused conservatively before the scene is
    exposed to the rest of the Universal Agent Core.
    """

    def __init__(
        self,
        providers: tuple[PerceptionProvider, ...] = (),
        element_fusion: ScreenElementFusion | None = None,
    ) -> None:
        self.providers = providers
        self.element_fusion = (
            element_fusion
            if element_fusion is not None
            else ScreenElementFusion()
        )

    def perceive(
        self,
        observation: EnvironmentObservation,
    ) -> ScreenScene:

        elements: list = []

        for provider in self.providers:
            elements.extend(
                provider.perceive(observation)
            )

        raw_elements = tuple(elements)
        fusion_result = self.element_fusion.fuse(
            raw_elements,
        )

        scene_metadata = dict(observation.metadata)
        scene_metadata["provider_count"] = len(self.providers)
        scene_metadata["raw_element_count"] = len(raw_elements)
        scene_metadata["element_count"] = len(
            fusion_result.elements
        )
        scene_metadata["merged_group_count"] = (
            fusion_result.merged_group_count
        )

        return ScreenScene(
            observation=observation,
            elements=fusion_result.elements,
            metadata=scene_metadata,
        )
