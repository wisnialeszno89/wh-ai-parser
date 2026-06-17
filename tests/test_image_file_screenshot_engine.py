import cv2
import numpy as np

from app.wh.vision.image_file_screenshot_engine import (
    ImageFileScreenshotEngine
)


def test_image_file_screenshot_engine():

    image = np.zeros(

        (

            1080,

            1920,

            3

        ),

        dtype=np.uint8

    )

    cv2.imwrite(

        "tmp.png",

        image

    )

    engine = (

        ImageFileScreenshotEngine()

    )

    screenshot = (

        engine.capture(

            "tmp.png"

        )

    )

    assert screenshot.width == 1920

    assert screenshot.height == 1080