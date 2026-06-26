from app.wh.runtime.vision.goal_confidence_level import (
    GoalConfidenceLevel
)


def test_goal_confidence_level():

    assert (

        GoalConfidenceLevel.LOW.value

        ==

        "low"

    )

    assert (

        GoalConfidenceLevel.MEDIUM.value

        ==

        "medium"

    )

    assert (

        GoalConfidenceLevel.HIGH.value

        ==

        "high"

    )

    assert (

        GoalConfidenceLevel.VERY_HIGH.value

        ==

        "very_high"

    )