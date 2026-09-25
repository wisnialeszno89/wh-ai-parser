from app.runtime.execution.interactions.interaction_action import (
    InteractionAction,
)
from app.runtime.execution.vision.bridges.execution_safety_gate import (
    ExecutionSafetyGate,
)
from app.runtime.execution.vision.models.control_type import (
    ControlType,
)
from app.runtime.execution.vision.models.logical_object import (
    LogicalObject,
)
from app.runtime.execution.vision.models.tracked_object import (
    TrackedObject,
    TrackedObjectStatus,
)


def make_track(
    control_type,
    *,
    confidence=0.9,
    observations=2,
    status=TrackedObjectStatus.STABLE,
):
    logical_object = LogicalObject(
        bounds=None,
        root_contour_index=0,
        member_contour_indices=(0,),
    )

    return TrackedObject(
        id="TO-TEST",
        object=logical_object,
        control_type=control_type,
        confidence=confidence,
        observation_count=observations,
        consecutive_observations=observations,
        status=status,
        stability=1.0,
    )


def test_icon_is_rejected():
    gate = ExecutionSafetyGate()

    track = make_track(ControlType.ICON)

    assert gate.can_execute(
        track,
        InteractionAction.CLICK,
    ) is False


def test_unknown_is_rejected():
    gate = ExecutionSafetyGate()

    track = make_track(ControlType.UNKNOWN)

    assert gate.can_execute(
        track,
        InteractionAction.CLICK,
    ) is False


def test_lost_button_is_rejected():
    gate = ExecutionSafetyGate()

    track = make_track(
        ControlType.BUTTON,
        status=TrackedObjectStatus.LOST,
    )

    assert gate.can_execute(
        track,
        InteractionAction.CLICK,
    ) is False


def test_new_button_is_rejected():
    gate = ExecutionSafetyGate()

    track = make_track(
        ControlType.BUTTON,
        observations=1,
        status=TrackedObjectStatus.NEW,
    )

    assert gate.can_execute(
        track,
        InteractionAction.CLICK,
    ) is False


def test_stable_button_is_allowed():
    gate = ExecutionSafetyGate()

    track = make_track(
        ControlType.BUTTON,
        confidence=0.71,
        observations=2,
        status=TrackedObjectStatus.STABLE,
    )

    assert gate.can_execute(
        track,
        InteractionAction.CLICK,
    ) is True


def test_zero_confidence_button_is_rejected():
    gate = ExecutionSafetyGate()

    track = make_track(
        ControlType.BUTTON,
        confidence=0.0,
    )

    assert gate.can_execute(
        track,
        InteractionAction.CLICK,
    ) is False


def test_unsupported_action_is_rejected():
    gate = ExecutionSafetyGate()

    track = make_track(ControlType.BUTTON)

    assert gate.can_execute(
        track,
        InteractionAction.WRITE,
    ) is False
