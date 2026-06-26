from app.wh.runtime.vision.goal_adaptive_mode_decision import (
    GoalAdaptiveModeDecision
)

from app.wh.runtime.vision.goal_risk_level import (
    GoalRiskLevel
)

from app.wh.runtime.vision.adaptive_execution_mode import (
    AdaptiveExecutionMode
)


def test_goal_adaptive_mode_decision():

    decision = (

        GoalAdaptiveModeDecision(

            goal_name="enable_rc2",

            risk_level=(

                GoalRiskLevel.LOW

            ),

            mode=(

                AdaptiveExecutionMode.NORMAL

            )

        )

    )

    assert (

        decision.goal_name

        ==

        "enable_rc2"

    )

    assert (

        decision.risk_level

        ==

        GoalRiskLevel.LOW

    )

    assert (

        decision.mode

        ==

        AdaptiveExecutionMode.NORMAL

    )