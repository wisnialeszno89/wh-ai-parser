from app.wh.runtime.vision.goal_decision import (
    GoalDecision
)

from app.wh.runtime.vision.goal_confidence_level import (
    GoalConfidenceLevel
)

from app.wh.runtime.vision.adaptive_execution_mode import (
    AdaptiveExecutionMode
)


def test_goal_decision():

    decision = (

        GoalDecision(

            goal_name="enable_rc2",

            confidence_level=(

                GoalConfidenceLevel.VERY_HIGH

            ),

            execution_mode=(

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

        decision.confidence_level

        ==

        GoalConfidenceLevel.VERY_HIGH

    )

    assert (

        decision.execution_mode

        ==

        AdaptiveExecutionMode.NORMAL

    )