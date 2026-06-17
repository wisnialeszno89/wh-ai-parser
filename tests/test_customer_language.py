from app.knowledge.text.customer_language import (
    normalize_token
)


def test_polish_p():

    assert (

        normalize_token(
            "P"
        )

        ==

        "RU"

    )


def test_german_dk():

    assert (

        normalize_token(
            "DK"
        )

        ==

        "RU"

    )


def test_german_fest():

    assert (

        normalize_token(
            "Fest"
        )

        ==

        "FIX"

    )