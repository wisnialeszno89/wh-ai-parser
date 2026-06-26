from app.wh.runtime.vision.alternative_strategy_engine import (
    AlternativeStrategyEngine
)

from app.wh.runtime.vision.alternative_strategy import (
    AlternativeStrategy
)


def test_alternative_strategy_engine():

    engine = (

        AlternativeStrategyEngine()

    )

    assert (

        engine.choose(

            "template_not_found"

        )

        ==

        AlternativeStrategy.OCR_FALLBACK

    )

    assert (

        engine.choose(

            "checkbox_failed"

        )

        ==

        AlternativeStrategy.CLICK_BY_COORDINATES

    )

    assert (

        engine.choose(

            "dropdown_failed"

        )

        ==

        AlternativeStrategy.TYPE_TEXT

    )

    assert (

        engine.choose(

            "unknown"

        )

        ==

        AlternativeStrategy.RETRY_SAME

    )