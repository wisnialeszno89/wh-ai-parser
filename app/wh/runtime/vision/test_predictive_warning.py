from app.wh.runtime.vision.predictive_warning import (
    PredictiveWarning
)


def test_predictive_warning():

    warning = (

        PredictiveWarning(

            reason="database_error",

            confidence=7

        )

    )

    assert (

        warning.reason

        ==

        "database_error"

    )

    assert (

        warning.confidence

        ==

        7

    )