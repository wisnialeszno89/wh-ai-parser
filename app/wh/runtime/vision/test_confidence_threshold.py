from app.wh.runtime.vision.confidence_threshold import (
    ConfidenceThreshold
)


def test_confidence_threshold():

    threshold = (

        ConfidenceThreshold(

            threshold=0.9

        )

    )

    assert (

        threshold.accepts(

            0.95

        )

        is True

    )

    assert (

        threshold.accepts(

            0.89

        )

        is False

    )