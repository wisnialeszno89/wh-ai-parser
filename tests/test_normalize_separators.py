from app.knowledge.text.normalize_separators import (
    normalize_separators
)


def test_plus():

    assert (

        normalize_separators(

            "FIX+RU+FIX"

        )

        ==

        "FIX RU FIX"

    )


def test_slash():

    assert (

        normalize_separators(

            "FIX/RU/FIX"

        )

        ==

        "FIX RU FIX"

    )


def test_dash():

    assert (

        normalize_separators(

            "FIX-RU-FIX"

        )

        ==

        "FIX RU FIX"

    )


def test_pipe():

    assert (

        normalize_separators(

            "FIX|RU|FIX"

        )

        ==

        "FIX RU FIX"

    )