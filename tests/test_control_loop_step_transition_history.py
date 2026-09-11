from app.agent.runtime.action_step_status import (
    ActionStepStatus,
)

from app.agent.runtime.action_step_transition import (
    ActionStepTransition,
)

from app.agent.runtime.control_loop_result import (
    ControlLoopResult,
)


def test_control_loop_result_records_step_transitions():

    transition = ActionStepTransition(
        action_name="test_action",
        from_status=ActionStepStatus.PENDING,
        to_status=ActionStepStatus.PREPARING,
    )

    result = ControlLoopResult(
        decisions=(),
        execution_results=(),
        success=True,
        step_transitions=(
            transition,
        ),
    )

    assert result.step_transitions == (
        transition,
    )

    assert result.transition_count == 1
