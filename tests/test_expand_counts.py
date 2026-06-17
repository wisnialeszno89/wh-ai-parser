from app.knowledge.text.expand_counts import (
    expand_counts
)


def test_2x_dk():

    assert (

        expand_counts(

            "2X DK"

        )

        ==

        "DK DK"

    )


def test_2xdk():

    assert (

        expand_counts(

            "2XDK"

        )

        ==

        "DK DK"

    )


def test_3xfix():

    assert (

        expand_counts(

            "3XFIX"

        )

        ==

        "FIX FIX FIX"

    )