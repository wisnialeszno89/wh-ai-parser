from app.wh.runtime.query.glass_aliases import (
    GlassAliases
)


def test_glass_aliases():

    aliases = GlassAliases()

    assert (

        aliases.normalize(

            "3SZYBY"

        )

        ==

        "3 SZYBY"

    )

    assert (

        aliases.normalize(

            "TRZYSZYBOWE"

        )

        ==

        "3 SZYBY"

    )

    assert (

        aliases.normalize(

            "PAKIET 3 SZYBY"

        )

        ==

        "3 SZYBY"

    )

    assert (

        aliases.normalize(

            "DWUSZYBOWE"

        )

        ==

        "2 SZYBY"

    )