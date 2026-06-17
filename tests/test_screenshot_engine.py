from app.wh.vision.screenshot_engine import (
    ScreenshotEngine
)


def test_screenshot_engine():

    engine = ScreenshotEngine()

    screenshot = engine.capture()

    assert screenshot.width == 1920

    assert screenshot.height == 1080