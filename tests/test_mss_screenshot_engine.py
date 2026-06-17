from app.wh.vision.mss_screenshot_engine import (
    MSSScreenshotEngine
)


def test_mss_screenshot_engine():

    engine = MSSScreenshotEngine()

    screenshot = engine.capture()

    assert screenshot.width == 1920

    assert screenshot.height == 1080

    assert screenshot.image.shape == (

        1080,

        1920,

        4

    )