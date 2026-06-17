from app.knowledge.text.text_to_schema import (
    text_to_schema
)


def test_two_space_x():

    schema = text_to_schema(

        "1500x1400 2 x DK"

    )

    assert len(
        schema.segments
    ) == 2


def test_two_without_space():

    schema = text_to_schema(

        "1500x1400 2xDK"

    )

    assert len(
        schema.segments
    ) == 2


def test_three_without_space():

    schema = text_to_schema(

        "1500x1400 3xFIX"

    )

    assert len(
        schema.segments
    ) == 3