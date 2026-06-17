from app.wh.runtime.query.profile_registry import (
    ProfileRegistry
)


def test_profile_registry():

    registry = ProfileRegistry()

    assert (

        registry.resolve(

            "SL82"

        )

        ==

        "VEKA SOFTLINE 82"

    )

    assert (

        registry.resolve(

            "VEKA82"

        )

        ==

        "VEKA SOFTLINE 82"

    )

    assert (

        registry.resolve(

            "SOFTLINE82"

        )

        ==

        "VEKA SOFTLINE 82"

    )