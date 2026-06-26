from app.wh.runtime.vision.goal_confidence import (
    GoalConfidence
)

from app.wh.runtime.vision.goal_confidence_level import (
    GoalConfidenceLevel
)


def test_goal_confidence():

    confidence = (

        GoalConfidence(

            goal_name="enable_rc2",

            level=(

                GoalConfidenceLevel.VERY_HIGH

            )

        )

    )

    assert (

        confidence.goal_name

        ==

        "enable_rc2"

    )

    assert (

        confidence.level

        ==

        GoalConfidenceLevel.VERY_HIGH

    )