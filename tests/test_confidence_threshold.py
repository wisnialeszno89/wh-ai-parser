from app.wh.vision.confidence_threshold import (
    ConfidenceThreshold
)


def test_confidence_threshold():

    assert (

        ConfidenceThreshold.DEFAULT

        ==

        0.90

    )

    assert (

        ConfidenceThreshold.LOW

        ==

        0.70

    )

    assert (

        ConfidenceThreshold.HIGH

        ==

        0.98

    )