from app.wh.runtime.vision.autonomous_decision import (
    AutonomousDecision
)

from app.wh.runtime.vision.adaptive_execution_mode import (
    AdaptiveExecutionMode
)

from app.wh.runtime.vision.confidence_level import (
    ConfidenceLevel
)


def test_autonomous_decision():

    decision = (

        AutonomousDecision(

            mode=(

                AdaptiveExecutionMode.NORMAL

            ),

            confidence_level=(

                ConfidenceLevel.VERY_HIGH

            ),

            confidence=150

        )

    )

    assert (

        decision.mode

        ==

        AdaptiveExecutionMode.NORMAL

    )

    assert (

        decision.confidence_level

        ==

        ConfidenceLevel.VERY_HIGH

    )

    assert (

        decision.confidence

        ==

        150

    )