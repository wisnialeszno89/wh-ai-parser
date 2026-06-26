from enum import (
    Enum
)


class AlternativeStrategy(

    Enum

):

    RETRY_SAME = (

        "retry_same"

    )

    CLICK_BY_COORDINATES = (

        "click_by_coordinates"

    )

    OCR_FALLBACK = (

        "ocr_fallback"

    )

    TYPE_TEXT = (

        "type_text"

    )

    REQUIRE_HUMAN = (

        "require_human"

    )