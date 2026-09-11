from app.agent.runtime.action_step_runtime_state import (
    ActionStepRuntimeState,
)

from app.agent.runtime.action_step_status import (
    ActionStepStatus,
)


def create_state(
    status: ActionStepStatus,
    attempts: int = 0,
    last_error: str = "",
) -> ActionStepRuntimeState:

    return ActionStepRuntimeState(
        step_index=3,
        action_name="test_action",
        status=status,
        attempts=attempts,
        last_error=last_error,
    )


def test_runtime_state_stores_current_step_state():

    state = create_state(
        ActionStepStatus.EXECUTING,
        attempts=2,
        last_error="Temporary failure.",
    )

    assert state.step_index == 3

    assert state.action_name == "test_action"

    assert (
        state.status
        == ActionStepStatus.EXECUTING
    )

    assert state.attempts == 2

    assert (
        state.last_error
        == "Temporary failure."
    )


def test_completed_state_is_terminal():

    state = create_state(
        ActionStepStatus.COMPLETED
    )

    assert state.is_terminal

    assert not state.can_resume


def test_skipped_state_is_terminal():

    state = create_state(
        ActionStepStatus.SKIPPED
    )

    assert state.is_terminal

    assert not state.can_resume


def test_stopped_state_is_terminal():

    state = create_state(
        ActionStepStatus.STOPPED
    )

    assert state.is_terminal

    assert not state.can_resume


def test_manual_review_state_is_terminal():

    state = create_state(
        ActionStepStatus.MANUAL_REVIEW
    )

    assert state.is_terminal

    assert not state.can_resume


def test_pending_state_can_resume():

    state = create_state(
        ActionStepStatus.PENDING
    )

    assert not state.is_terminal

    assert state.can_resume


def test_preparing_state_can_resume():

    state = create_state(
        ActionStepStatus.PREPARING
    )

    assert not state.is_terminal

    assert state.can_resume


def test_ready_state_can_resume():

    state = create_state(
        ActionStepStatus.READY
    )

    assert not state.is_terminal

    assert state.can_resume


def test_executing_state_can_resume():

    state = create_state(
        ActionStepStatus.EXECUTING
    )

    assert not state.is_terminal

    assert state.can_resume


def test_verifying_state_can_resume():

    state = create_state(
        ActionStepStatus.VERIFYING
    )

    assert not state.is_terminal

    assert state.can_resume


def test_failed_state_can_resume():

    state = create_state(
        ActionStepStatus.FAILED
    )

    assert not state.is_terminal

    assert state.can_resume
