import pytest

from app.agent.runtime.action_step_lifecycle import (
    ActionStepLifecycle,
)

from app.agent.runtime.action_step_status import (
    ActionStepStatus,
)


def create_lifecycle():

    return ActionStepLifecycle()


@pytest.mark.parametrize(
    (
        "current",
        "target",
    ),
    [
        (
            ActionStepStatus.PENDING,
            ActionStepStatus.PREPARING,
        ),
        (
            ActionStepStatus.PREPARING,
            ActionStepStatus.READY,
        ),
        (
            ActionStepStatus.READY,
            ActionStepStatus.EXECUTING,
        ),
        (
            ActionStepStatus.EXECUTING,
            ActionStepStatus.VERIFYING,
        ),
        (
            ActionStepStatus.VERIFYING,
            ActionStepStatus.COMPLETED,
        ),
        (
            ActionStepStatus.EXECUTING,
            ActionStepStatus.FAILED,
        ),
        (
            ActionStepStatus.FAILED,
            ActionStepStatus.SKIPPED,
        ),
        (
            ActionStepStatus.FAILED,
            ActionStepStatus.MANUAL_REVIEW,
        ),
        (
            ActionStepStatus.FAILED,
            ActionStepStatus.STOPPED,
        ),
    ],
)
def test_lifecycle_allows_valid_transition(
    current,
    target,
):

    lifecycle = create_lifecycle()

    assert (
        lifecycle.can_transition(
            current,
            target,
        )
        is True
    )


@pytest.mark.parametrize(
    (
        "current",
        "target",
    ),
    [
        (
            ActionStepStatus.PENDING,
            ActionStepStatus.COMPLETED,
        ),
        (
            ActionStepStatus.PENDING,
            ActionStepStatus.EXECUTING,
        ),
        (
            ActionStepStatus.READY,
            ActionStepStatus.COMPLETED,
        ),
        (
            ActionStepStatus.COMPLETED,
            ActionStepStatus.EXECUTING,
        ),
        (
            ActionStepStatus.SKIPPED,
            ActionStepStatus.EXECUTING,
        ),
        (
            ActionStepStatus.MANUAL_REVIEW,
            ActionStepStatus.READY,
        ),
        (
            ActionStepStatus.STOPPED,
            ActionStepStatus.PREPARING,
        ),
    ],
)
def test_lifecycle_rejects_invalid_transition(
    current,
    target,
):

    lifecycle = create_lifecycle()

    assert (
        lifecycle.can_transition(
            current,
            target,
        )
        is False
    )


def test_lifecycle_returns_target_status():

    lifecycle = create_lifecycle()

    result = lifecycle.transition(
        ActionStepStatus.PENDING,
        ActionStepStatus.PREPARING,
    )

    assert (
        result
        == ActionStepStatus.PREPARING
    )


def test_lifecycle_raises_for_invalid_transition():

    lifecycle = create_lifecycle()

    with pytest.raises(
        ValueError,
        match=(
            "Invalid action step status transition"
        ),
    ):

        lifecycle.transition(
            ActionStepStatus.PENDING,
            ActionStepStatus.COMPLETED,
        )


@pytest.mark.parametrize(
    "status",
    [
        ActionStepStatus.COMPLETED,
        ActionStepStatus.SKIPPED,
        ActionStepStatus.MANUAL_REVIEW,
        ActionStepStatus.STOPPED,
    ],
)
def test_lifecycle_recognizes_terminal_status(
    status,
):

    lifecycle = create_lifecycle()

    assert (
        lifecycle.is_terminal(status)
        is True
    )


@pytest.mark.parametrize(
    "status",
    [
        ActionStepStatus.PENDING,
        ActionStepStatus.PREPARING,
        ActionStepStatus.READY,
        ActionStepStatus.EXECUTING,
        ActionStepStatus.VERIFYING,
        ActionStepStatus.FAILED,
    ],
)
def test_lifecycle_recognizes_non_terminal_status(
    status,
):

    lifecycle = create_lifecycle()

    assert (
        lifecycle.is_terminal(status)
        is False
    )


def test_lifecycle_exposes_allowed_transitions():

    lifecycle = create_lifecycle()

    transitions = (
        lifecycle.allowed_transitions(
            ActionStepStatus.FAILED
        )
    )

    assert (
        ActionStepStatus.SKIPPED
        in transitions
    )

    assert (
        ActionStepStatus.MANUAL_REVIEW
        in transitions
    )

    assert (
        ActionStepStatus.STOPPED
        in transitions
    )
