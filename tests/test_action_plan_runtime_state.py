from app.agent.runtime.action_plan_runtime_state import (
    ActionPlanRuntimeState,
)

from app.agent.runtime.action_plan_status import (
    ActionPlanStatus,
)


def test_default_plan_runtime_state_is_created():

    state = ActionPlanRuntimeState()

    assert (
        state.status
        == ActionPlanStatus.CREATED
    )

    assert (
        state.current_step_index
        is None
    )

    assert state.total_steps == 0

    assert state.completed_steps == 0

    assert state.failed_steps == 0

    assert state.skipped_steps == 0

    assert (
        state.requires_manual_review
        is False
    )

    assert state.stopped is False


def test_running_plan_is_not_finished():

    state = ActionPlanRuntimeState(
        status=ActionPlanStatus.RUNNING,
    )

    assert state.is_finished is False


def test_completed_plan_is_finished():

    state = ActionPlanRuntimeState(
        status=ActionPlanStatus.COMPLETED,
    )

    assert state.is_finished is True


def test_failed_plan_is_finished():

    state = ActionPlanRuntimeState(
        status=ActionPlanStatus.FAILED,
    )

    assert state.is_finished is True


def test_stopped_plan_is_finished():

    state = ActionPlanRuntimeState(
        status=ActionPlanStatus.STOPPED,
        stopped=True,
    )

    assert state.is_finished is True


def test_manual_review_plan_is_finished():

    state = ActionPlanRuntimeState(
        status=ActionPlanStatus.MANUAL_REVIEW,
        requires_manual_review=True,
    )

    assert state.is_finished is True


def test_processed_steps():

    state = ActionPlanRuntimeState(
        total_steps=10,
        completed_steps=4,
        failed_steps=2,
        skipped_steps=1,
    )

    assert state.processed_steps == 7


def test_remaining_steps():

    state = ActionPlanRuntimeState(
        total_steps=10,
        completed_steps=4,
        failed_steps=2,
        skipped_steps=1,
    )

    assert state.remaining_steps == 3


def test_remaining_steps_never_negative():

    state = ActionPlanRuntimeState(
        total_steps=2,
        completed_steps=2,
        failed_steps=1,
        skipped_steps=1,
    )

    assert state.remaining_steps == 0
