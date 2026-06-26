from app.wh.runtime.vision.goal_risk import (
    GoalRisk
)

from app.wh.runtime.vision.goal_risk_level import (
    GoalRiskLevel
)


def test_goal_risk():

    risk = (

        GoalRisk(

            goal_name="enable_rc2",

            risk_level=(

                GoalRiskLevel.LOW

            ),

            success_rate=0.9

        )

    )

    assert (

        risk.goal_name

        ==

        "enable_rc2"

    )

    assert (

        risk.risk_level

        ==

        GoalRiskLevel.LOW

    )

    assert (

        risk.success_rate

        ==

        0.9

    )