from app.wh.runtime.vision.goal_risk_level import (
    GoalRiskLevel
)


def test_goal_risk_level():

    assert (

        GoalRiskLevel.LOW.value

        ==

        "low"

    )

    assert (

        GoalRiskLevel.MEDIUM.value

        ==

        "medium"

    )

    assert (

        GoalRiskLevel.HIGH.value

        ==

        "high"

    )