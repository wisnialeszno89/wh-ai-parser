from app.wh.vision.screen_locator import (
    ScreenLocator
)


def test_screen_locator_v2():

    locator = ScreenLocator()

    location = locator.locate(

        "profile_combobox.png"

    )

    assert location == (

        100,

        200

    )