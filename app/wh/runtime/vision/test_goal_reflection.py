from app.wh.runtime.vision.goal_reflection import (
    GoalReflection
)


def test_goal_reflection():

    reflection = (

        GoalReflection(

            goal_name="enable_rc2",

            success=True,

            conclusion="goal_completed"

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