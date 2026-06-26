from app.wh.runtime.vision.vision_reasoning_engine import (
    VisionReasoningEngine
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)

from app.wh.runtime.vision.gui_goal import (
    GUIGoal
)


def test_vision_reasoning_engine():

    brain = (

        ProjectBrain()

    )

    engine = (

        VisionReasoningEngine()

    )

    goal = (

        GUIGoal(

            "enable_rc2"

        )

    )

    decision = (

        engine.decide(

            goal,

            brain

        )

    )

    assert (

        decision.execute

        is True

    )

    brain.goal_memory.remember(

        goal

    )

    decision = (

        engine.decide(

            goal,

            brain

        )

    )

    assert (

        decision.execute

        is False

    )

    assert (

        decision.reason

        ==

        "already_completed"

    )