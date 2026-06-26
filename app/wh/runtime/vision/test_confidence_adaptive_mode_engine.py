from app.wh.runtime.vision.confidence_adaptive_mode_engine import (
    ConfidenceAdaptiveModeEngine
)

from app.wh.runtime.vision.confidence_engine import (
    ConfidenceEngine
)

from app.wh.runtime.vision.adaptive_execution_mode import (
    AdaptiveExecutionMode
)


def test_confidence_adaptive_mode_engine():

    confidence_engine = (

        ConfidenceEngine()

    )

    engine = (

        ConfidenceAdaptiveModeEngine()

    )

    assert (

        engine.decide(

            confidence_engine.evaluate(

                150

            )

        ).mode

        ==

        AdaptiveExecutionMode.NORMAL

    )

    assert (

        engine.decide(

            confidence_engine.evaluate(

                30

            )

        ).mode

        ==

        AdaptiveExecutionMode.CAREFUL_MODE

    )

    assert (

        engine.decide(

            confidence_engine.evaluate(

                10

            )

        ).mode

        ==

        AdaptiveExecutionMode.SAFE_MODE

    )

    assert (

        engine.decide(

            confidence_engine.evaluate(

                1

            )

        ).mode

        ==

        AdaptiveExecutionMode.HUMAN_REVIEW_MODE

    )