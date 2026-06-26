from app.wh.runtime.vision.goal_decision_engine import (
    GoalDecisionEngine
)

from app.wh.runtime.vision.goal_confidence import (
    GoalConfidence
)

from app.wh.runtime.vision.goal_confidence_level import (
    GoalConfidenceLevel
)

from app.wh.runtime.vision.adaptive_execution_mode import (
    AdaptiveExecutionMode
)


def test_goal_decision_engine():

    engine = (

        GoalDecisionEngine()

    )

    confidence = (

        GoalConfidence(

            goal_name="enable_rc2",

            level=(

                GoalConfidenceLevel.VERY_HIGH

            )

        )

    )

    result = (

        engine.decide(

            confidence

        )

    )

    assert (

        result.goal_name

        ==

        "enable_rc2"

    )

    assert (

        result.execution_mode

        ==

        AdaptiveExecutionMode.NORMAL

    )