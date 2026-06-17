import numpy as np

from app.wh.vision.screenshot import (
    Screenshot
)


def test_screenshot_pixels():

    screenshot = Screenshot(

        width=1920,

        height=1080,

        image=np.zeros(

            (1080, 1920, 3),

            dtype=np.uint8

        )

    )

    assert screenshot.image.shape == (

        1080,

        1920,

        3

    )