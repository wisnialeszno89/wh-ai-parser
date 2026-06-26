from app.wh.runtime.vision.global_best_strategy import (
    GlobalBestStrategy
)

from app.wh.runtime.vision.alternative_strategy import (
    AlternativeStrategy
)


def test_global_best_strategy():

    result = (

        GlobalBestStrategy(

            strategy=(

                AlternativeStrategy.OCR_FALLBACK

            ),

            confidence=143

        )

    )

    assert (

        result.strategy

        ==

        AlternativeStrategy.OCR_FALLBACK

    )

    assert (

        result.confidence

        ==

        143

    )