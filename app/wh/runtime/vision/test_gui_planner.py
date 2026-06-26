from app.wh.runtime.vision.gui_goal import (
    GUIGoal
)

from app.wh.runtime.vision.gui_planner import (
    GUIPlanner
)


def test_gui_planner():

    planner = (

        GUIPlanner()

    )

    plan = (

        planner.create_plan(

            GUIGoal(

                "enable_rc2"

            )

        )

    )

    assert (

        len(

            plan.steps

        )

        ==

        2

    )

    assert (

        plan.steps[0]

        ==

        "goto_hardware"

    )

    assert (

        plan.steps[1]

        ==

        "enable_rc2"

    )