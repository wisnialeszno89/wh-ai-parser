from app.knowledge.text.text_to_schema import (
    text_to_schema
)


def test_fix_ru_fix():

    schema = text_to_schema(

        "1500x1400 FIX RU FIX"

    )

    assert (

        schema.width_mm

        ==

        1500
    )

    assert (

        schema.height_mm

        ==

        1400
    )

    assert len(
        schema.segments
    ) == 3


def test_german_abbreviation():

    schema = text_to_schema(

        "1000x1200 DK"

    )

    assert len(
        schema.segments
    ) == 1

    assert (

        schema.segments[0][
            "opening"
        ]

        ==

        "tilt_turn"

    )


def test_mixed_language():

    schema = text_to_schema(

        "1500x1400 Fest DK Fest"

    )

    assert len(
        schema.segments
    ) == 3
    
def test_plus_separator():

    schema = text_to_schema(

        "1500x1400 FIX+RU+FIX"

    )

    assert len(
        schema.segments
    ) == 3


def test_slash_separator():

    schema = text_to_schema(

        "1500x1400 FIX/RU/FIX"

    )

    assert len(
        schema.segments
    ) == 3


def test_dash_separator():

    schema = text_to_schema(

        "1500x1400 FIX-RU-FIX"

    )

    assert len(
        schema.segments
    ) == 3


def test_pipe_separator():

    schema = text_to_schema(

        "1500x1400 FIX|RU|FIX"

    )

    assert len(
        schema.segments
    ) == 3


def test_german_separator():

    schema = text_to_schema(

        "1500x1400 Fest+DK+Fest"

    )

    assert len(
        schema.segments
    ) == 3