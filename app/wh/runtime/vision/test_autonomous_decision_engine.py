from app.wh.runtime.vision.autonomous_decision_engine import (
    AutonomousDecisionEngine
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)

from app.wh.runtime.vision.adaptive_execution_mode import (
    AdaptiveExecutionMode
)

from app.wh.runtime.vision.confidence_level import (
    ConfidenceLevel
)


def test_autonomous_decision_engine():

    brain = (

        ProjectBrain()

    )

    engine = (

        AutonomousDecisionEngine()

    )

    result = (

        engine.decide(

            150,

            brain

        )

    )

    assert (

        result.mode

        ==

        AdaptiveExecutionMode.NORMAL

    )

    assert (

        result.confidence_level

        ==

        ConfidenceLevel.VERY_HIGH

    )

    assert (

        result.confidence

        ==

        150

    )