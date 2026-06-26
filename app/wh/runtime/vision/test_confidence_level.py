from app.wh.runtime.vision.confidence_level import (
    ConfidenceLevel
)


def test_confidence_level():

    assert (

        ConfidenceLevel.LOW.value

        ==

        "low"

    )

    assert (

        ConfidenceLevel.MEDIUM.value

        ==

        "medium"

    )

    assert (

        ConfidenceLevel.HIGH.value

        ==

        "high"

    )

    assert (

        ConfidenceLevel.VERY_HIGH.value

        ==

        "very_high"

    )