from app.wh.runtime.vision.global_recovery_decision import (
    GlobalRecoveryDecision
)

from app.wh.runtime.vision.alternative_strategy import (
    AlternativeStrategy
)


def test_global_recovery_decision():

    decision = (

        GlobalRecoveryDecision(

            strategy=(

                AlternativeStrategy.OCR_FALLBACK

            ),

            confidence=99

        )

    )

    assert (

        decision.strategy

        ==

        AlternativeStrategy.OCR_FALLBACK

    )

    assert (

        decision.confidence

        ==

        99

    )