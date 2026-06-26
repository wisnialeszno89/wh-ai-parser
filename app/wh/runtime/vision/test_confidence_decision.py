from app.wh.runtime.vision.confidence_decision import (
    ConfidenceDecision
)

from app.wh.runtime.vision.confidence_level import (
    ConfidenceLevel
)


def test_confidence_decision():

    decision = (

        ConfidenceDecision(

            level=(

                ConfidenceLevel.HIGH

            ),

            confidence=25

        )

    )

    assert (

        decision.level

        ==

        ConfidenceLevel.HIGH

    )

    assert (

        decision.confidence

        ==

        25

    )