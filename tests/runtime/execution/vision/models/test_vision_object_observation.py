from app.runtime.execution.vision.models.control_type import ControlType
from app.runtime.execution.vision.models.logical_object import LogicalObject
from app.runtime.execution.vision.models.rect import Rect
from app.runtime.execution.vision.models.vision_object_observation import (
    VisionObjectObservation,
)


def test_vision_object_observation_contains_semantic_observation() -> None:
    logical_object = LogicalObject(
        bounds=Rect(
            x=100,
            y=100,
            width=32,
            height=32,
        ),
        root_contour_index=1,
        member_contour_indices=(1, 2),
    )

    observation = VisionObjectObservation(
        logical_object=logical_object,
        control_type=ControlType.ICON,
        confidence=0.669,
    )

    assert observation.logical_object is logical_object
    assert observation.control_type is ControlType.ICON
    assert observation.confidence == 0.669
