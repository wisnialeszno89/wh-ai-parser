from app.wh.runtime.vision.prediction_strategy import (
    PredictionStrategy
)


def test_prediction_strategy():

    assert (

        PredictionStrategy.NORMAL.value

        ==

        "normal"

    )

    assert (

        PredictionStrategy.EXTRA_LOGGING.value

        ==

        "extra_logging"

    )

    assert (

        PredictionStrategy.SAFE_MODE.value

        ==

        "safe_mode"

    )

    assert (

        PredictionStrategy.REQUIRE_HUMAN_REVIEW.value

        ==

        "require_human_review"

    )