import numpy as np

from app.wh.vision.screenshot_engine import (
    ScreenshotEngine
)


def test_screenshot_image_type():

    engine = ScreenshotEngine()

    screenshot = engine.capture()

    assert isinstance(

        screenshot.image,

        np.ndarray

    )

    assert screenshot.image.dtype == np.uint8