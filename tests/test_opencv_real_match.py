from app.wh.vision.screenshot_engine import (
    ScreenshotEngine
)


def test_real_screenshot():

    engine = ScreenshotEngine()

    screenshot = engine.capture()

    assert screenshot.width > 0

    assert screenshot.height > 0