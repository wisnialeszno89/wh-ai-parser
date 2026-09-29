from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.perception.perception_provider import (
    PerceptionProvider,
)
from app.agent.perception.screen_element import (
    ScreenElement,
)

from app.runtime.execution.vision.models.tracked_object import (
    TrackedObject,
    TrackedObjectStatus,
)
from app.runtime.execution.vision.models.control_type import (
    ControlType,
)
from app.runtime.execution.vision.pipeline.vision_pipeline import (
    VisionPipeline,
)


class WindowHubVisionProvider(PerceptionProvider):
    """
    WindowHub-specific perception adapter.

    Converts legacy VisionPipeline tracked objects into
    generic Universal Agent Core ScreenElement objects.
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

        context = self.vision_pipeline.observe(
            window=observation.metadata.get("window_rect"),
            screenshot=observation.metadata.get("screenshot"),
        )

        scene_graph = context.scene_graph
        observation.metadata["execution_runtime"] = {
            "robot_tracked_objects": tuple(
                context.tracked_objects or ()
            ),
            "gui_object_root": (
                scene_graph.root
                if scene_graph is not None
                else None
            ),
        }

        return tuple(
            self._to_screen_element(tracked_object)
            for tracked_object in context.tracked_objects
            if tracked_object.status is not TrackedObjectStatus.LOST
        )

    @staticmethod
    def _to_screen_element(
        tracked_object: TrackedObject,
    ) -> ScreenElement:

        bounds = tracked_object.object.bounds
        control_type = tracked_object.control_type

        return ScreenElement(
            kind=(
                control_type.value
                if control_type is not None
                else "unknown"
            ),
            label=None,
            x=bounds.x,
            y=bounds.y,
            width=bounds.width,
            height=bounds.height,
            confidence=tracked_object.confidence,
            metadata={
                "source": "windowhub_vision_pipeline",
                "tracked_object_id": tracked_object.id,
                "control_type": (
                    control_type.value
                    if control_type is not None
                    else None
                ),
                "interactive": (
                    control_type == ControlType.BUTTON
                ),
                "status": tracked_object.status.value,
                "stability": tracked_object.stability,
                "consecutive_observations": (
                    tracked_object.consecutive_observations
                ),
            },
        )
