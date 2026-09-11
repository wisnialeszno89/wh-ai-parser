from app.agent.runtime.action_step_status import (
    ActionStepStatus,
)

from app.agent.runtime.action_step_transition import (
    ActionStepTransition,
)


def test_action_step_transition_records_state_change():

    transition = ActionStepTransition(
        action_name="test_action",
        from_status=ActionStepStatus.PENDING,
        to_status=ActionStepStatus.PREPARING,
    )

    assert (
        transition.action_name
        == "test_action"
    )

    assert (
        transition.from_status
        == ActionStepStatus.PENDING
    )

    assert (
        transition.to_status
        == ActionStepStatus.PREPARING
    )
