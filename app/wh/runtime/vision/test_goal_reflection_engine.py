from app.wh.runtime.vision.goal_reflection_engine import (
    GoalReflectionEngine
)

from app.wh.runtime.vision.gui_goal import (
    GUIGoal
)


def test_goal_reflection_engine():

    engine = (

        GoalReflectionEngine()

    )

    reflection = (

        engine.reflect(

            GUIGoal(

                "enable_rc2"

            ),

            True

        )

    )

    assert (

        reflection.goal_name

        ==

        "enable_rc2"

    )

    assert (

        reflection.success

        is True

    )

    assert (

        reflection.conclusion

        ==

        "goal_completed"

    )