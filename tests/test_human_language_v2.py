from app.knowledge.text.text_to_schema import (
    text_to_schema
)


def test_2_space_x():

    schema = text_to_schema(

        "1500x1400 2 x DK"

    )

    assert len(
        schema.segments
    ) == 2


def test_2xdk():

    schema = text_to_schema(

        "1500x1400 2xDK"

    )

    assert len(
        schema.segments
    ) == 2


def test_2_szt():

    schema = text_to_schema(

        "1500x1400 2 szt DK"

    )

    assert len(
        schema.segments
    ) == 2


def test_2_szt_dot():

    schema = text_to_schema(

        "1500x1400 2 szt. DK"

    )

    assert len(
        schema.segments
    ) == 2


def test_3_szt_fix():

    schema = text_to_schema(

        "1500x1400 3 szt FIX"

    )

    assert len(
        schema.segments
    ) == 3