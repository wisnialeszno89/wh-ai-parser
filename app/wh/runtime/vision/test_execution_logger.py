from app.wh.runtime.vision.execution_logger import (
    ExecutionLogger
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)

from app.wh.runtime.vision.gui_goal import (
    GUIGoal
)

from app.wh.runtime.vision.vision_decision import (
    VisionDecision
)


def test_execution_logger():

    brain = (

        ProjectBrain()

    )

    logger = (

        ExecutionLogger()

    )

    goal = (

        GUIGoal(

            "enable_rc2"

        )

    )

    decision = (

        VisionDecision(

            execute=True,

            reason="not_completed"

        )

    )

    logger.log(

        goal,

        decision,

        True,

        brain

    )

    assert (

        brain.execution_history.count()

        ==

        1

    )

    record = (

        brain.execution_history.records[0]

    )

    assert (

        record.goal

        ==

        "enable_rc2"

    )

    assert (

        record.success

        is True

    )

    assert (

        record.reason

        ==

        "not_completed"

    )