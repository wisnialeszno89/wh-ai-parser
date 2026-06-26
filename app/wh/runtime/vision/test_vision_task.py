from app.wh.runtime.vision.vision_task import (
    VisionTask
)

from app.wh.runtime.vision.gui_goal import (
    GUIGoal
)


def test_vision_task():

    task = (

        VisionTask(

            "configure_security"

        )

    )

    task.goals.append(

        GUIGoal(

            "enable_rc2"

        )

    )

    task.goals.append(

        GUIGoal(

            "enable_contacts"

        )

    )

    assert (

        len(

            task.goals

        )

        ==

        2

    )