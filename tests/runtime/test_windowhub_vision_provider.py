from types import SimpleNamespace

from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.environment.environment_state import (
    EnvironmentState,
)
from app.agent.perception.interaction_capability import (
    InteractionCapability,
)
from app.agent.perception.windowhub_vision_provider import (
    WindowHubVisionProvider,
)
from app.runtime.execution.vision.models.control_type import (
    ControlType,
)
from app.runtime.execution.vision.models.logical_object import (
    LogicalObject,
)
from app.runtime.execution.vision.models.rect import Rect
from app.runtime.execution.vision.models.tracked_object import (
    TrackedObject,
)


class EmptyVisionPipeline:
    def __init__(self):
        self.kwargs = None

    def observe(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(
            tracked_objects=None,
            scene_graph=None,
        )


def test_windowhub_provider_handles_empty_tracked_objects():
    pipeline = EmptyVisionPipeline()

    observation = EnvironmentObservation(
        state=EnvironmentState(),
        metadata={
            "window_rect": "window",
            "screenshot": "screenshot",
        },
    )

    elements = WindowHubVisionProvider(
        vision_pipeline=pipeline,
    ).perceive(observation)

    assert elements == ()

    runtime = observation.metadata["execution_runtime"]

    assert runtime["robot_tracked_objects"] == ()
    assert runtime["gui_object_root"] is None
    assert pipeline.kwargs == {
        "window": "window",
        "screenshot": "screenshot",
    }


def make_tracked_object(
    object_id: str,
    control_type: ControlType,
) -> TrackedObject:
    return TrackedObject(
        id=object_id,
        object=LogicalObject(
            bounds=Rect(
                x=10,
                y=20,
                width=24,
                height=24,
            ),
            root_contour_index=0,
            member_contour_indices=(0, 1),
        ),
        control_type=control_type,
        confidence=0.9,
        consecutive_observations=2,
    )


def test_windowhub_provider_separates_visual_type_from_interaction_capability():
    button = WindowHubVisionProvider._to_screen_element(
        make_tracked_object("TO-BUTTON", ControlType.BUTTON),
    )
    icon = WindowHubVisionProvider._to_screen_element(
        make_tracked_object("TO-ICON", ControlType.ICON),
    )

    assert button.kind == "button"
    assert button.interaction_capability is InteractionCapability.CLICKABLE
    assert button.metadata["interaction_capability"] == "clickable"
    assert button.metadata["interactive"] is True

    assert icon.kind == "icon"
    assert icon.interaction_capability is InteractionCapability.UNKNOWN
    assert icon.metadata["interaction_capability"] == "unknown"
    assert icon.metadata["interactive"] is False

