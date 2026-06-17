from app.wh.runtime.query.opening_aliases import (
    OpeningAliases
)


def test_opening_aliases():

    aliases = OpeningAliases()

    assert (

        aliases.normalize(

            "RU+FIX"

        )

        ==

        "RU|FIX"

    )

    assert (

        aliases.normalize(

            "RU + FIX"

        )

        ==

        "RU|FIX"

    )

    assert (

        aliases.normalize(

            "RU FIX"

        )

        ==

        "RU|FIX"

    )

    assert (

        aliases.normalize(

            "R+F"

        )

        ==

        "RU|FIX"

    )