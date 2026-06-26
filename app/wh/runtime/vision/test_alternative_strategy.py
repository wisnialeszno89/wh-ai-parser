from app.wh.runtime.vision.alternative_strategy import (
    AlternativeStrategy
)


def test_alternative_strategy():

    assert (

        AlternativeStrategy.RETRY_SAME.value

        ==

        "retry_same"

    )

    assert (

        AlternativeStrategy.CLICK_BY_COORDINATES.value

        ==

        "click_by_coordinates"

    )

    assert (

        AlternativeStrategy.OCR_FALLBACK.value

        ==

        "ocr_fallback"

    )

    assert (

        AlternativeStrategy.TYPE_TEXT.value

        ==

        "type_text"

    )

    assert (

        AlternativeStrategy.REQUIRE_HUMAN.value

        ==

        "require_human"

    )