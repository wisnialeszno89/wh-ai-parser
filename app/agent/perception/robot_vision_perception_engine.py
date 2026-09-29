from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)

from app.agent.perception.perception_engine import (
    PerceptionEngine,
)

from app.agent.perception.screen_element import (
    ScreenElement,
)

from app.runtime.execution.vision.models.tracked_object import (
    TrackedObject,
    TrackedObjectStatus,
)

from app.runtime.execution.vision.pipeline.vision_pipeline import (
    VisionPipeline,
)


class RobotVisionPerceptionEngine(PerceptionEngine):
    """
    Agent perception adapter backed by the robot VisionPipeline.

    The agent sees only generic ScreenScene / ScreenElement objects.
    Robot-specific tracked-object data is preserved in metadata.
    """

    def __init__(
        self,
        vision_pipeline: VisionPipeline | None = None,
    ) -> None:
        super().__init__()
        self.vision_pipeline = (
            vision_pipeline
            if vision_pipeline is not None
            else VisionPipeline()
        )

    def perceive(
        self,
        observation: EnvironmentObservation,
    ):
        context = self.vision_pipeline.observe()

        elements = tuple(
            self._to_screen_element(
                tracked_object,
            )
            for tracked_object in context.tracked_objects
            if tracked_object.status
            is not TrackedObjectStatus.LOST
        )

        scene = super().perceive(observation)

        return type(scene)(
            observation=observation,
            elements=elements,
            metadata={
                "vision_source": "VisionPipeline",
                "tracked_object_count": len(
                    context.tracked_objects
                ),
            },
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
                "tracked_object_id": tracked_object.id,
                "control_type": tracked_object.control_type,
                "status": tracked_object.status.value,
                "stability": tracked_object.stability,
                "consecutive_observations": (
                    tracked_object.consecutive_observations
                ),
            },
        )
