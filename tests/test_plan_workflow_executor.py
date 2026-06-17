from app.wh.runtime.window_plan import (
    WindowPlan
)

from app.wh.runtime.plan_workflow_executor import (
    PlanWorkflowExecutor
)


def test_plan_workflow_executor():

    plan = WindowPlan()

    plan.add_window(

        1500,

        1400,

        "basic_window"

    )

    plan.add_window(

        1200,

        1200,

        "fix_window"

    )

    executor = PlanWorkflowExecutor()

    result = executor.execute(

        plan

    )

    assert result is True