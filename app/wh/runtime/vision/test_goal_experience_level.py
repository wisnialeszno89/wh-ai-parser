from app.wh.runtime.vision.goal_experience_level import (
    GoalExperienceLevel
)


def test_goal_experience_level():

    assert (

        GoalExperienceLevel.LOW.value

        ==

        "low"

    )

    assert (

        GoalExperienceLevel.MEDIUM.value

        ==

        "medium"

    )

    assert (

        GoalExperienceLevel.HIGH.value

        ==

        "high"

    )

    assert (

        GoalExperienceLevel.VERY_HIGH.value

        ==

        "very_high"

    )