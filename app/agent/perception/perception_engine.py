from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)

from app.agent.perception.screen_scene import (
    ScreenScene,
)


class PerceptionEngine:
    """
    Converts environment observations into semantic scenes.

    The first implementation intentionally performs only
    minimal interpretation.

    Concrete perception providers may later enrich the scene
    with elements detected through:
    - accessibility APIs
    - browser DOM
    - OCR
    - computer vision
    """

    def perceive(
        self,
        observation: EnvironmentObservation,
    ) -> ScreenScene:

        return ScreenScene(
            observation=observation
        )
