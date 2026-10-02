from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.perception.perception_engine import (
    PerceptionEngine,
)
from app.agent.perception.screen_element import (
    ScreenElement,
)
from app.agent.perception.screen_element_fusion import (
    ScreenElementFusion,
)
from app.runtime.execution.vision.models.tracked_object import (
    TrackedObject,
    TrackedObjectStatus,
)
from app.runtime.execution.vision.pipeline.vision_pipeline import (
    VisionPipeline,
)


class LegacyRobotVisionProvider:
    """
    Compatibility adapter for the legacy RobotVisionPerceptionEngine path.

    New Universal Agent Core code should use WindowHubVisionProvider through
    the provider-driven PerceptionEngine.
    """

    def __init__(
        self,
        vision_pipeline: VisionPipeline | None = None,
    ) -> None:
        self.vision_pipeline = (
            vision_pipeline
            if vision_pipeline is not None
            else VisionPipeline()
        )

    def perceive(
        self,
        observation: EnvironmentObservation,
    ) -> tuple[ScreenElement, ...]:
        context = self.vision_pipeline.observe()

        tracked_objects = tuple(
            context.tracked_objects or ()
        )

        return tuple(
            self._to_screen_element(tracked_object)
            for tracked_object in tracked_objects
            if tracked_object.status
            is not TrackedObjectStatus.LOST
        )

    @staticmethod
    def _to_screen_element(
        tracked_object: TrackedObject,
    ) -> ScreenElement:
        bounds = tracked_object.object.bounds

        return ScreenElement(
            kind=(
                tracked_object.control_type
                or "unknown"
            ),
            label=tracked_object.id,
            x=bounds.x,
            y=bounds.y,
            width=bounds.width,
            height=bounds.height,
            confidence=tracked_object.confidence,
            metadata={
                "source": "legacy_robot_vision",
                "tracked_object_id": tracked_object.id,
                "control_type": tracked_object.control_type,
                "status": tracked_object.status.value,
                "stability": tracked_object.stability,
                "consecutive_observations": (
                    tracked_object.consecutive_observations
                ),
            },
        )


class RobotVisionPerceptionEngine(PerceptionEngine):
    """
    Legacy compatibility facade.

    Prefer the provider-driven PerceptionEngine with
    WindowHubVisionProvider for all new Universal Agent Core code.
    """

    def __init__(
        self,
        vision_pipeline: VisionPipeline | None = None,
    ) -> None:
        super().__init__(
            providers=(
                LegacyRobotVisionProvider(
                    vision_pipeline=vision_pipeline,
                ),
            ),
            element_fusion=ScreenElementFusion(),
        )

    def perceive(
        self,
        observation: EnvironmentObservation,
    ):
        return super().perceive(observation)
