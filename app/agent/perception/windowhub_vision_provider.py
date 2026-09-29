from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.perception.interaction_capability import (
    InteractionCapability,
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

        tracked_objects = tuple(
            context.tracked_objects or ()
        )

        scene_graph = context.scene_graph
        observation.metadata["execution_runtime"] = {
            "robot_tracked_objects": tracked_objects,
            "gui_object_root": (
                scene_graph.root
                if scene_graph is not None
                else None
            ),
        }

        return tuple(
            self._to_screen_element(tracked_object)
            for tracked_object in tracked_objects
            if tracked_object.status is not TrackedObjectStatus.LOST
        )

    @staticmethod
    def _interaction_capability(
        control_type,
    ) -> InteractionCapability:
        if control_type == ControlType.BUTTON:
            return InteractionCapability.CLICKABLE

        return InteractionCapability.UNKNOWN

    @classmethod
    def _to_screen_element(
        cls,
        tracked_object: TrackedObject,
    ) -> ScreenElement:

        bounds = tracked_object.object.bounds
        control_type = tracked_object.control_type
        interaction_capability = cls._interaction_capability(
            control_type,
        )

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
            interaction_capability=interaction_capability,
            metadata={
                "source": "windowhub_vision_pipeline",
                "tracked_object_id": tracked_object.id,
                "control_type": (
                    control_type.value
                    if control_type is not None
                    else None
                ),
                "interaction_capability": (
                    interaction_capability.value
                ),
                "interactive": (
                    interaction_capability
                    is InteractionCapability.CLICKABLE
                ),
                "status": tracked_object.status.value,
                "stability": tracked_object.stability,
                "consecutive_observations": (
                    tracked_object.consecutive_observations
                ),
            },
        )
