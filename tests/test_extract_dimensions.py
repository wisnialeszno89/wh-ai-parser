from app.knowledge.text.extract_dimensions import (
    extract_dimensions
)


def test_normal():

    assert (

        extract_dimensions(

            "1500x1400"

        )

        ==

        (

            1500,

            1400

        )

    )


def test_space():

    assert (

        extract_dimensions(

            "1500 x 1400"

        )

        ==

        (

            1500,

            1400

        )

    )


def test_text():

    assert (

        extract_dimensions(

            "okno 1500x1400 FIX RU"

        )

        ==

        (

            1500,

            1400

        )

    )