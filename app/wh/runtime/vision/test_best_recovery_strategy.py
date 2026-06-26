from app.wh.runtime.vision.best_recovery_strategy import (
    BestRecoveryStrategy
)

from app.wh.runtime.vision.alternative_strategy import (
    AlternativeStrategy
)


def test_best_recovery_strategy():

    strategy = (

        BestRecoveryStrategy(

            strategy=(

                AlternativeStrategy.OCR_FALLBACK

            ),

            confidence=12

        )

    )

    assert (

        strategy.strategy

        ==

        AlternativeStrategy.OCR_FALLBACK

    )

    assert (

        strategy.confidence

        ==

        12

    )