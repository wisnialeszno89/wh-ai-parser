from app.runtime.execution.vision.models.logical_object import LogicalObject
from app.runtime.execution.vision.models.rect import Rect
from app.runtime.execution.vision.models.tracked_object import (
    TrackedObject,
    TrackedObjectStatus,
)


def make_object() -> LogicalObject:
    return LogicalObject(
        bounds=Rect(x=100, y=100, width=20, height=20),
        root_contour_index=1,
        member_contour_indices=(1, 2),
    )


def test_tracked_object_defaults():
    obj = make_object()

    tracked = TrackedObject(
        id="TO-0001",
        object=obj,
    )

    assert tracked.id == "TO-0001"
    assert tracked.object is obj
    assert tracked.control_type is None
    assert tracked.confidence == 0.0
    assert tracked.first_seen == 0
    assert tracked.last_seen == 0
    assert tracked.observation_count == 0
    assert tracked.consecutive_observations == 0
    assert tracked.status is TrackedObjectStatus.NEW
    assert tracked.stability == 0.0


def test_tracked_object_accepts_tracking_state():
    obj = make_object()

    tracked = TrackedObject(
        id="TO-0001",
        object=obj,
        control_type="icon",
        confidence=0.8,
        first_seen=1,
        last_seen=5,
        observation_count=5,
        consecutive_observations=5,
        status=TrackedObjectStatus.STABLE,
        stability=1.0,
    )

    assert tracked.control_type == "icon"
    assert tracked.confidence == 0.8
    assert tracked.first_seen == 1
    assert tracked.last_seen == 5
    assert tracked.observation_count == 5
    assert tracked.consecutive_observations == 5
    assert tracked.status is TrackedObjectStatus.STABLE
    assert tracked.stability == 1.0
