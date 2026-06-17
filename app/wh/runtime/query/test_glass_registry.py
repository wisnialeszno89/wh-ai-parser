from app.wh.runtime.query.glass_registry import (
    GlassRegistry
)


def test_glass_registry():

    registry = GlassRegistry()

    assert (

        registry.resolve(

            "TRZYSZYBOWE"

        )

        ==

        "3 SZYBY"

    )

    assert (

        registry.resolve(

            "PAKIET 3 SZYBY"

        )

        ==

        "3 SZYBY"

    )

    assert (

        registry.resolve(

            "DWUSZYBOWE"

        )

        ==

        "2 SZYBY"

    )