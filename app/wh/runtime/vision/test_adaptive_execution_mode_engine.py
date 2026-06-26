from app.wh.runtime.vision.adaptive_execution_mode_engine import (
    AdaptiveExecutionModeEngine
)

from app.wh.runtime.vision.prediction_strategy import (
    PredictionStrategy
)

from app.wh.runtime.vision.adaptive_execution_mode import (
    AdaptiveExecutionMode
)


def test_adaptive_execution_mode_engine():

    engine = (

        AdaptiveExecutionModeEngine()

    )

    assert (

        engine.decide(

            PredictionStrategy.NORMAL

        )

        ==

        AdaptiveExecutionMode.NORMAL

    )

    assert (

        engine.decide(

            PredictionStrategy.EXTRA_LOGGING

        )

        ==

        AdaptiveExecutionMode.CAREFUL_MODE

    )

    assert (

        engine.decide(

            PredictionStrategy.SAFE_MODE

        )

        ==

        AdaptiveExecutionMode.SAFE_MODE

    )

    assert (

        engine.decide(

            PredictionStrategy.REQUIRE_HUMAN_REVIEW

        )

        ==

        AdaptiveExecutionMode.HUMAN_REVIEW_MODE

    )