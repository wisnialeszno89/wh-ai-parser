from app.wh.vision.screen_locator import (
    ScreenLocator
)


def test_screen_locator_v3():

    locator = ScreenLocator()

    location = locator.locate(

        "profile"

    )

    assert location == (

        100,

        200

    )