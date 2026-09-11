import pytest

from app.agent.agent_action import (
    AgentAction,
)

from app.agent.agent_intent import (
    AgentIntent,
)

from app.agent.planning.action_plan import (
    ActionPlan,
)

from app.agent.planning.action_step import (
    ActionStep,
)

from app.agent.runtime.action_plan_runtime import (
    ActionPlanRuntime,
)

from app.agent.runtime.action_step_status import (
    ActionStepStatus,
)


def create_action(
    name: str,
) -> AgentAction:

    return AgentAction(
        name=name,
        description=name,
    )


def create_plan(
    *actions: AgentAction,
) -> ActionPlan:

    return ActionPlan(
        intent=AgentIntent.CREATE_QUOTE,
        steps=tuple(
            ActionStep(
                index=index,
                action=action,
            )
            for index, action
            in enumerate(actions)
        ),
        confidence=1.0,
    )


def test_runtime_creates_state_for_every_step():

    plan = create_plan(
        create_action("first"),
        create_action("second"),
    )

    runtime = ActionPlanRuntime(
        plan
    )

    assert len(
        runtime.step_states
    ) == 2


def test_runtime_states_follow_plan_order():

    plan = create_plan(
        create_action("first"),
        create_action("second"),
    )

    runtime = ActionPlanRuntime(
        plan
    )

    assert [
        state.action_name
        for state
        in runtime.step_states
    ] == [
        "first",
        "second",
    ]


def test_runtime_can_start_step():

    plan = create_plan(
        create_action("first"),
    )

    runtime = ActionPlanRuntime(
        plan
    )

    state = runtime.start_step(
        0
    )

    assert (
        runtime.current_step_index
        == 0
    )

    assert (
        runtime.current_step
        == state
    )


def test_runtime_rejects_unknown_step():

    runtime = ActionPlanRuntime(
        create_plan(
            create_action("first"),
        )
    )

    with pytest.raises(
        ValueError
    ):

        runtime.get_step_state(
            99
        )


def test_runtime_can_update_step_status():

    runtime = ActionPlanRuntime(
        create_plan(
            create_action("first"),
        )
    )

    runtime.start_step(
        0
    )

    runtime.mark_ready(
        0
    )

    assert (
        runtime
        .get_step_state(0)
        .status
        == ActionStepStatus.READY
    )


def test_runtime_tracks_terminal_step():

    runtime = ActionPlanRuntime(
        create_plan(
            create_action("first"),
        )
    )

    runtime.start_step(
        0
    )

    runtime.mark_ready(
        0
    )

    runtime.mark_executing(
        0
    )

    runtime.mark_verifying(
        0
    )

    runtime.mark_completed(
        0
    )

    assert (
        runtime.current_step
        is None
    )


def test_runtime_reports_complete_plan():

    runtime = ActionPlanRuntime(
        create_plan(
            create_action("first"),
        )
    )

    runtime.start_step(
        0
    )

    runtime.mark_ready(
        0
    )

    runtime.mark_executing(
        0
    )

    runtime.mark_verifying(
        0
    )

    runtime.mark_completed(
        0
    )

    assert runtime.is_complete


def test_runtime_reports_successful_plan():

    runtime = ActionPlanRuntime(
        create_plan(
            create_action("first"),
        )
    )

    runtime.start_step(
        0
    )

    runtime.mark_ready(
        0
    )

    runtime.mark_executing(
        0
    )

    runtime.mark_verifying(
        0
    )

    runtime.mark_completed(
        0
    )

    assert runtime.is_successful


def test_runtime_reports_manual_review():

    runtime = ActionPlanRuntime(
        create_plan(
            create_action("first"),
        )
    )

    runtime.start_step(
        0
    )

    runtime.mark_ready(
        0
    )

    runtime.require_manual_review(
        0,
        reason="Needs human input.",
    )

    assert (
        runtime.requires_manual_review
    )


def test_runtime_reports_stopped_plan():

    runtime = ActionPlanRuntime(
        create_plan(
            create_action("first"),
        )
    )

    runtime.start_step(
        0
    )

    runtime.mark_ready(
        0
    )

    runtime.mark_stopped(
        0,
        reason="Execution stopped.",
    )

    assert runtime.is_stopped


def test_runtime_rejects_restarting_terminal_step():

    runtime = ActionPlanRuntime(
        create_plan(
            create_action("first"),
        )
    )

    runtime.start_step(
        0
    )

    runtime.mark_ready(
        0
    )

    runtime.mark_executing(
        0
    )

    runtime.mark_verifying(
        0
    )

    runtime.mark_completed(
        0
    )

    with pytest.raises(
        ValueError
    ):

        runtime.start_step(
            0
        )
