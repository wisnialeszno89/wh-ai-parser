from app.wh.runtime.vision.goal_reasoning_engine import (
    GoalReasoningEngine
)

from app.wh.runtime.vision.goal_memory import (
    GoalMemory
)

from app.wh.runtime.vision.gui_goal import (
    GUIGoal
)


def test_goal_reasoning_engine():

    memory = (

        GoalMemory()

    )

    goal = (

        GUIGoal(

            "enable_rc2"

        )

    )

    engine = (

        GoalReasoningEngine()

    )

    assert (

        engine.should_execute(

            goal,

            memory

        )

        is True

    )

    memory.remember(

        goal

    )

    assert (

        engine.should_execute(

            goal,

            memory

        )

        is False

    )