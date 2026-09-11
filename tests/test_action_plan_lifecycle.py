import pytest

from app.agent.runtime.action_plan_lifecycle import (
    ActionPlanLifecycle,
)

from app.agent.runtime.action_plan_status import (
    ActionPlanStatus,
)


def test_plan_starts_created():

    lifecycle = ActionPlanLifecycle()

    assert (
        lifecycle.status
        == ActionPlanStatus.CREATED
    )

    assert lifecycle.transitions == ()


def test_plan_can_start_running():

    lifecycle = ActionPlanLifecycle()

    transition = lifecycle.transition_to(
        ActionPlanStatus.RUNNING
    )

    assert (
        transition.from_status
        == ActionPlanStatus.CREATED
    )

    assert (
        transition.to_status
        == ActionPlanStatus.RUNNING
    )

    assert (
        lifecycle.status
        == ActionPlanStatus.RUNNING
    )


@pytest.mark.parametrize(
    "terminal_status",
    [
        ActionPlanStatus.COMPLETED,
        ActionPlanStatus.FAILED,
        ActionPlanStatus.STOPPED,
        ActionPlanStatus.MANUAL_REVIEW,
    ],
)
def test_running_plan_can_reach_terminal_status(
    terminal_status,
):

    lifecycle = ActionPlanLifecycle()

    lifecycle.transition_to(
        ActionPlanStatus.RUNNING
    )

    lifecycle.transition_to(
        terminal_status
    )

    assert (
        lifecycle.status
        == terminal_status
    )

    assert lifecycle.is_terminal


@pytest.mark.parametrize(
    "terminal_status",
    [
        ActionPlanStatus.COMPLETED,
        ActionPlanStatus.FAILED,
        ActionPlanStatus.STOPPED,
        ActionPlanStatus.MANUAL_REVIEW,
    ],
)
def test_terminal_plan_cannot_transition_again(
    terminal_status,
):

    lifecycle = ActionPlanLifecycle()

    lifecycle.transition_to(
        ActionPlanStatus.RUNNING
    )

    lifecycle.transition_to(
        terminal_status
    )

    with pytest.raises(
        ValueError
    ):

        lifecycle.transition_to(
            ActionPlanStatus.RUNNING
        )


def test_created_plan_cannot_complete_directly():

    lifecycle = ActionPlanLifecycle()

    with pytest.raises(
        ValueError
    ):

        lifecycle.transition_to(
            ActionPlanStatus.COMPLETED
        )


def test_transition_reason_is_recorded():

    lifecycle = ActionPlanLifecycle()

    lifecycle.transition_to(
        ActionPlanStatus.RUNNING,
        reason="Plan execution started.",
    )

    transition = (
        lifecycle.transitions[-1]
    )

    assert (
        transition.reason
        == "Plan execution started."
    )
