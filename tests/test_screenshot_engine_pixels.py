import numpy as np

from app.wh.vision.screenshot_engine import (
    ScreenshotEngine
)


def test_screenshot_engine_pixels():

    engine = ScreenshotEngine()

    screenshot = engine.capture()

    assert screenshot.width == 1920

    assert screenshot.height == 1080

    assert screenshot.image.shape == (

        1080,

        1920,

        3

    )

    assert isinstance(

        screenshot.image,

        np.ndarray

    )