from app.wh.runtime.window_plan import (
    WindowPlan
)


def test_window_plan():

    plan = WindowPlan()

    plan.add_window(

        1500,

        1400,

        "basic_window"

    )

    assert len(

        plan.windows

    ) == 1