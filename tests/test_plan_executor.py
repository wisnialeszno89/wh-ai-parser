from app.wh.runtime.window_plan import (
    WindowPlan
)

from app.wh.runtime.plan_executor import (
    PlanExecutor
)


def test_plan_executor():

    plan = WindowPlan()

    plan.add_window(

        1500,

        1400,

        "basic_window"

    )

    executor = PlanExecutor()

    assert executor is not None