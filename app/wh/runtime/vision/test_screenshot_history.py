from app.wh.runtime.vision.screenshot_history import (
    ScreenshotHistory
)


def test_screenshot_history():

    history = (

        ScreenshotHistory()

    )

    history.remember(

        "before.png"

    )

    history.remember(

        "after.png"

    )

    assert (

        history.count()

        ==

        2

    )