from app.runtime.execution.vision.models.control_type import ControlType
from app.runtime.execution.vision.models.logical_object import LogicalObject
from app.runtime.execution.vision.models.rect import Rect
from app.runtime.execution.vision.models.vision_object_observation import (
    VisionObjectObservation,
)
from app.runtime.execution.vision.tracking.temporal_object_tracker import (
    TemporalObjectTracker,
)


def make_observation(
    *,
    x: int = 100,
    y: int = 100,
    width: int = 32,
    height: int = 32,
    control_type: ControlType = ControlType.ICON,
    confidence: float = 0.669,
) -> VisionObjectObservation:
    logical_object = LogicalObject(
        bounds=Rect(
            x=x,
            y=y,
            width=width,
            height=height,
        ),
        root_contour_index=1,
        member_contour_indices=(1, 2),
    )

    return VisionObjectObservation(
        logical_object=logical_object,
        control_type=control_type,
        confidence=confidence,
    )


def test_tracker_preserves_semantic_identity_between_observations() -> None:
    tracker = TemporalObjectTracker()

    first = tracker.update(
        [make_observation()]
    )

    second = tracker.update(
        [make_observation()]
    )

    assert first[0].id == "TO-0001"
    assert second[0].id == "TO-0001"

    assert second[0].control_type == ControlType.ICON
    assert second[0].confidence == 0.669
    assert second[0].observation_count == 2


def test_tracker_updates_semantic_observation_on_existing_track() -> None:
    tracker = TemporalObjectTracker()

    tracker.update(
        [
            make_observation(
                control_type=ControlType.ICON,
                confidence=0.60,
            )
        ]
    )

    second = tracker.update(
        [
            make_observation(
                control_type=ControlType.BUTTON,
                confidence=0.91,
            )
        ]
    )

    assert second[0].id == "TO-0001"
    assert second[0].control_type == ControlType.BUTTON
    assert second[0].confidence == 0.91
