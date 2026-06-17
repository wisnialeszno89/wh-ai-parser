from app.wh.runtime.query.profile_aliases import (
    ProfileAliases
)


def test_profile_aliases():

    aliases = ProfileAliases()

    assert (

        aliases.normalize(

            "VEKA82"

        )

        ==

        "VEKA SOFTLINE 82"

    )

    assert (

        aliases.normalize(

            "SL82"

        )

        ==

        "VEKA SOFTLINE 82"

    )

    assert (

        aliases.normalize(

            "SOFTLINE82"

        )

        ==

        "VEKA SOFTLINE 82"

    )