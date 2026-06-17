from unittest.mock import (
    MagicMock
)

from app.wh.runtime.actions.action_plan import (
    ActionPlan
)

from app.wh.runtime.actions.action import (
    Action
)

from app.wh.runtime.actions.action_plan_executor import (
    ActionPlanExecutor
)


def test_action_plan_executor():

    executor = (

        ActionPlanExecutor()

    )

    executor.executor = (

        MagicMock()

    )

    plan = (

        ActionPlan()

    )

    plan.add(

        Action(

            "frame",

            "frame_button.png"

        )

    )

    plan.add(

        Action(

            "glass",

            "glass_button.png"

        )

    )

    result = (

        executor.execute(

            plan

        )

    )

    assert (

        executor.executor.execute_action.call_count

        == 2

    )

    assert result is True