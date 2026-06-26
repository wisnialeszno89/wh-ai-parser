from app.wh.runtime.vision.confidence_engine import (
    ConfidenceEngine
)

from app.wh.runtime.vision.confidence_level import (
    ConfidenceLevel
)


def test_confidence_engine():

    engine = (

        ConfidenceEngine()

    )

    assert (

        engine.evaluate(

            2

        ).level

        ==

        ConfidenceLevel.LOW

    )

    assert (

        engine.evaluate(

            7

        ).level

        ==

        ConfidenceLevel.MEDIUM

    )

    assert (

        engine.evaluate(

            30

        ).level

        ==

        ConfidenceLevel.HIGH

    )

    assert (

        engine.evaluate(

            150

        ).level

        ==

        ConfidenceLevel.VERY_HIGH

    )