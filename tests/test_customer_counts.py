from app.knowledge.text.text_to_schema import (
    text_to_schema
)


def test_two_dk():

    schema = text_to_schema(

        "1500x1400 2x DK"

    )

    assert len(
        schema.segments
    ) == 2


def test_three_fix():

    schema = text_to_schema(

        "1500x1400 3x FIX"

    )

    assert len(
        schema.segments
    ) == 3


def test_two_polish():

    schema = text_to_schema(

        "1500x1400 2x P"

    )

    assert len(
        schema.segments
    ) == 2


def test_four_ru():

    schema = text_to_schema(

        "1500x1400 4x RU"

    )

    assert len(
        schema.segments
    ) == 4