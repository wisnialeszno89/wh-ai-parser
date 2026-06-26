from app.wh.runtime.vision.goal_confidence_engine import (
    GoalConfidenceEngine
)

from app.wh.runtime.vision.goal_risk import (
    GoalRisk
)

from app.wh.runtime.vision.goal_experience import (
    GoalExperience
)

from app.wh.runtime.vision.goal_risk_level import (
    GoalRiskLevel
)

from app.wh.runtime.vision.goal_experience_level import (
    GoalExperienceLevel
)

from app.wh.runtime.vision.goal_confidence_level import (
    GoalConfidenceLevel
)


def test_goal_confidence_engine():

    engine = (

        GoalConfidenceEngine()

    )

    risk = (

        GoalRisk(

            goal_name="enable_rc2",

            risk_level=(

                GoalRiskLevel.LOW

            ),

            success_rate=0.9

        )

    )

    experience = (

        GoalExperience(

            goal_name="enable_rc2",

            level=(

                GoalExperienceLevel.HIGH

            ),

            total_executions=50

        )

    )

    confidence = (

        engine.evaluate(

            risk,

            experience

        )

    )

    assert (

        confidence.level

        ==

        GoalConfidenceLevel.VERY_HIGH

    )