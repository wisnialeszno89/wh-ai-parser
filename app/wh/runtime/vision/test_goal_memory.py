from app.wh.runtime.vision.goal_memory import (
    GoalMemory
)

from app.wh.runtime.vision.gui_goal import (
    GUIGoal
)


def test_goal_memory():

    memory = (

        GoalMemory()

    )

    goal = (

        GUIGoal(

            "enable_rc2"

        )

    )

    memory.remember(

        goal

    )

    assert (

        memory.contains(

            "enable_rc2"

        )

        is True

    )

    assert (

        memory.contains(

            "enable_contacts"

        )

        is False

    )