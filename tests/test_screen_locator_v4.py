from app.wh.vision.screen_locator import (
    ScreenLocator
)


def test_screen_locator_v4():

    locator = ScreenLocator()

    result = locator.locate(

        "profile"

    )

    assert result.x > 0

    assert result.y > 0

    assert result.confidence >= 0.9