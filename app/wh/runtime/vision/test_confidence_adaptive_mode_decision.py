from app.wh.runtime.vision.confidence_adaptive_mode_decision import (
    ConfidenceAdaptiveModeDecision
)

from app.wh.runtime.vision.adaptive_execution_mode import (
    AdaptiveExecutionMode
)

from app.wh.runtime.vision.confidence_level import (
    ConfidenceLevel
)


def test_confidence_adaptive_mode_decision():

    decision = (

        ConfidenceAdaptiveModeDecision(

            level=(

                ConfidenceLevel.HIGH

            ),

            mode=(

                AdaptiveExecutionMode.NORMAL

            )

        )

    )

    assert (

        decision.level

        ==

        ConfidenceLevel.HIGH

    )

    assert (

        decision.mode

        ==

        AdaptiveExecutionMode.NORMAL

    )