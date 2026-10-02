from app.runtime.execution.verification import (
    ExecutionVerifier,
)
from app.runtime.execution.vision.models.control_type import ControlType
from app.runtime.execution.vision.models.logical_object import LogicalObject
from app.runtime.execution.vision.models.rect import Rect
from app.runtime.execution.vision.models.tracked_object import (
    TrackedObject,
    TrackedObjectStatus,
)


def make_tracked_object(
    *,
    bounds=Rect(100, 100, 100, 40),
    control_type=ControlType.BUTTON,
    confidence=0.90,
    consecutive_observations=2,
    status=TrackedObjectStatus.STABLE,
):
    logical_object = LogicalObject(
        bounds=bounds,
        root_contour_index=1,
        member_contour_indices=(1, 2),
    )

    return TrackedObject(
        id="TO-TEST",
        object=logical_object,
        control_type=control_type,
        confidence=confidence,
        consecutive_observations=consecutive_observations,
        status=status,
    )


def test_verifier_accepts_same_stable_button():
    tracked = make_tracked_object()

    verifier = ExecutionVerifier(
        min_confidence=0.50,
        min_iou=0.70,
    )

    result = verifier.verify(
        tracked_object=tracked,
        expected_control_type=ControlType.BUTTON,
        expected_bounds=Rect(100, 100, 100, 40),
    )

    assert result.verified is True
    assert result.reason == "Target verified"
    assert result.iou == 1.0


def test_verifier_accepts_small_target_movement():
    tracked = make_tracked_object(
        bounds=Rect(102, 101, 100, 40),
    )

    verifier = ExecutionVerifier(
        min_confidence=0.50,
        min_iou=0.70,
    )

    result = verifier.verify(
        tracked_object=tracked,
        expected_control_type=ControlType.BUTTON,
        expected_bounds=Rect(100, 100, 100, 40),
    )

    assert result.verified is True
    assert result.iou >= 0.70


def test_verifier_rejects_lost_target():
    tracked = make_tracked_object(
        status=TrackedObjectStatus.LOST,
    )

    verifier = ExecutionVerifier()

    result = verifier.verify(
        tracked_object=tracked,
        expected_control_type=ControlType.BUTTON,
        expected_bounds=Rect(100, 100, 100, 40),
    )

    assert result.verified is False
    assert result.reason == "Tracked object is lost"


def test_verifier_rejects_changed_control_type():
    tracked = make_tracked_object(
        control_type=ControlType.ICON,
    )

    verifier = ExecutionVerifier()

    result = verifier.verify(
        tracked_object=tracked,
        expected_control_type=ControlType.BUTTON,
        expected_bounds=Rect(100, 100, 100, 40),
    )

    assert result.verified is False
    assert result.reason == "Control type changed"


def test_verifier_rejects_low_confidence():
    tracked = make_tracked_object(
        confidence=0.40,
    )

    verifier = ExecutionVerifier(
        min_confidence=0.50,
    )

    result = verifier.verify(
        tracked_object=tracked,
        expected_control_type=ControlType.BUTTON,
        expected_bounds=Rect(100, 100, 100, 40),
    )

    assert result.verified is False
    assert result.reason == "Confidence below verification threshold"


def test_verifier_rejects_insufficient_observations():
    tracked = make_tracked_object(
        consecutive_observations=1,
    )

    verifier = ExecutionVerifier(
        min_consecutive_observations=2,
    )

    result = verifier.verify(
        tracked_object=tracked,
        expected_control_type=ControlType.BUTTON,
        expected_bounds=Rect(100, 100, 100, 40),
    )

    assert result.verified is False
    assert result.reason == "Insufficient consecutive observations"


def test_verifier_rejects_changed_geometry():
    tracked = make_tracked_object(
        bounds=Rect(400, 400, 100, 40),
    )

    verifier = ExecutionVerifier(
        min_iou=0.70,
    )

    result = verifier.verify(
        tracked_object=tracked,
        expected_control_type=ControlType.BUTTON,
        expected_bounds=Rect(100, 100, 100, 40),
    )

    assert result.verified is False
    assert result.reason == "Target geometry changed"
    assert result.iou == 0.0
