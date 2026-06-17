import numpy as np

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

    assert isinstance(

        screenshot,

        np.ndarray

    )

    assert screenshot.shape == (

        1080,

        1920,

        3

    )