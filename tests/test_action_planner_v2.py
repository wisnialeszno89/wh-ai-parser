from types import (
    SimpleNamespace
)

from app.wh.runtime.action_planner_v2 import (
    ActionPlannerV2
)


def test_action_planner_v2():

    construction = (

        SimpleNamespace()

    )

    planner = (

        ActionPlannerV2()

    )

    plan = (

        planner.plan(

            construction

        )

    )

    assert len(

        plan.actions

    ) == 3