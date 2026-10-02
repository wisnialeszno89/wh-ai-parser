from app.runtime.execution.vision.models.logical_object import LogicalObject
from app.runtime.execution.vision.models.rect import Rect
from app.runtime.execution.vision.models.tracked_object import (
    TrackedObjectStatus,
)
from app.runtime.execution.vision.tracking.temporal_object_tracker import (
    TemporalObjectTracker,
)


def make_object(
    x: int,
    y: int,
    width: int = 20,
    height: int = 20,
) -> LogicalObject:
    return LogicalObject(
        bounds=Rect(
            x=x,
            y=y,
            width=width,
            height=height,
        ),
        root_contour_index=1,
        member_contour_indices=(1, 2),
    )


def test_first_observation_creates_new_track() -> None:
    tracker = TemporalObjectTracker()

    tracks = tracker.update(
        [make_object(100, 100)]
    )

    assert len(tracks) == 1

    tracked = tracks[0]

    assert tracked.id == "TO-0001"
    assert tracked.status is TrackedObjectStatus.NEW
    assert tracked.observation_count == 1
    assert tracked.consecutive_observations == 1


def test_second_matching_observation_keeps_track_identity() -> None:
    tracker = TemporalObjectTracker()

    first = tracker.update(
        [make_object(100, 100)]
    )

    second = tracker.update(
        [make_object(100, 100)]
    )

    assert len(first) == 1
    assert len(second) == 1

    assert first[0].id == "TO-0001"
    assert second[0].id == "TO-0001"

    assert second[0].status is TrackedObjectStatus.STABLE
    assert second[0].observation_count == 2
    assert second[0].consecutive_observations == 2


def test_moved_observation_keeps_track_identity() -> None:
    tracker = TemporalObjectTracker(
        match_iou_threshold=0.3,
    )

    first = tracker.update(
        [make_object(100, 100)]
    )

    second = tracker.update(
        [make_object(105, 105)]
    )

    assert len(first) == 1
    assert len(second) == 1

    assert first[0].id == "TO-0001"
    assert second[0].id == "TO-0001"

    assert second[0].object.bounds.x == 105
    assert second[0].object.bounds.y == 105
    assert second[0].observation_count == 2


def test_moved_observation_sets_moved_status() -> None:
    tracker = TemporalObjectTracker(
        match_iou_threshold=0.3,
    )

    tracker.update(
        [make_object(100, 100)]
    )

    moved = tracker.update(
        [make_object(105, 105)]
    )

    assert len(moved) == 1
    assert moved[0].id == "TO-0001"
    assert moved[0].status is TrackedObjectStatus.MOVED
    assert moved[0].object.bounds.x == 105
    assert moved[0].object.bounds.y == 105


def test_missing_observation_does_not_immediately_lose_track() -> None:
    tracker = TemporalObjectTracker(
        match_iou_threshold=0.3,
    )

    tracker.update(
        [make_object(100, 100)]
    )

    missing = tracker.update([])

    assert len(missing) == 1
    assert missing[0].id == "TO-0001"
    assert missing[0].status is not TrackedObjectStatus.LOST
    assert missing[0].observation_count == 1


def test_track_becomes_lost_after_three_missing_frames() -> None:
    tracker = TemporalObjectTracker(
        match_iou_threshold=0.3,
    )

    tracker.update(
        [make_object(100, 100)]
    )

    tracker.update([])
    tracker.update([])

    lost = tracker.update([])

    assert len(lost) == 1
    assert lost[0].id == "TO-0001"
    assert lost[0].status is TrackedObjectStatus.LOST
    assert lost[0].observation_count == 1


def test_multiple_objects_keep_identity_when_observation_order_changes() -> None:
    tracker = TemporalObjectTracker(
        match_iou_threshold=0.5,
    )

    first = tracker.update(
        [
            make_object(100, 100),
            make_object(200, 100),
            make_object(300, 100),
        ]
    )

    second = tracker.update(
        [
            make_object(300, 100),
            make_object(100, 100),
            make_object(200, 100),
        ]
    )

    assert len(first) == 3
    assert len(second) == 3

    first_by_x = {
        track.object.bounds.x: track.id
        for track in first
    }

    second_by_x = {
        track.object.bounds.x: track.id
        for track in second
    }

    assert second_by_x[100] == first_by_x[100]
    assert second_by_x[200] == first_by_x[200]
    assert second_by_x[300] == first_by_x[300]

    assert all(
        track.status is TrackedObjectStatus.STABLE
        for track in second
    )
