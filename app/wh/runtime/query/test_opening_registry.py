from app.wh.runtime.query.opening_registry import (
    OpeningRegistry
)


def test_opening_registry():

    registry = OpeningRegistry()

    assert (

        registry.resolve(

            "RU+FIX"

        )

        ==

        "RU|FIX"

    )

    assert (

        registry.resolve(

            "RU FIX"

        )

        ==

        "RU|FIX"

    )

    assert (

        registry.resolve(

            "R+F"

        )

        ==

        "RU|FIX"

    )

    assert (

        registry.resolve(

            "RU|FIX"

        )

        ==

        "RU|FIX"

    )