from app.wh.runtime.vision.autonomous_failure_manager import (
    AutonomousFailureManager
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)

from app.wh.runtime.vision.gui_goal import (
    GUIGoal
)


def test_autonomous_failure_manager():

    brain = (

        ProjectBrain()

    )

    brain.gui_state.current_dialog = (

        "glass"

    )

    manager = (

        AutonomousFailureManager()

    )

    result = (

        manager.handle(

            GUIGoal(

                "enable_rc2"

            ),

            "dialog_not_found",

            brain

        )

    )

    assert (

        result

        is True

    )

    assert (

        brain.failure_history.count()

        ==

        1

    )

    assert (

        brain.gui_state.current_dialog

        is None

    )