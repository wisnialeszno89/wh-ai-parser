import numpy as np

from app.wh.vision.fake_screenshot_engine import (
    FakeScreenshotEngine
)


def test_fake_screenshot_engine():

    engine = FakeScreenshotEngine()

    screenshot = engine.capture()

    assert screenshot.width == 1920

    assert screenshot.height == 1080

    assert isinstance(

        screenshot.image,

        np.ndarray

    )

    assert screenshot.image.shape == (

        1080,

        1920,

        3

    )