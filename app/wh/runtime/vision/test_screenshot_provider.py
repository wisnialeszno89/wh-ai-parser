from app.wh.runtime.vision.screenshot_provider import (
    ScreenshotProvider
)


def test_screenshot_provider():

    provider = (

        ScreenshotProvider()

    )

    screenshot = (

        provider.capture()

    )

    assert (

        screenshot

        is None

    )