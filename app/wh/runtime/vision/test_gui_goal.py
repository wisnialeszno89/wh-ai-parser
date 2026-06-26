from app.wh.runtime.vision.gui_goal import (
    GUIGoal
)


def test_gui_goal():

    goal = (

        GUIGoal(

            "enable_rc2"

        )

    )

    assert (

        goal.name

        ==

        "enable_rc2"

    )