import cv2

from app.wh.vision.mss_screenshot_engine import (
    MSSScreenshotEngine
)


def test_save_real_screen():

    screenshot = (

        MSSScreenshotEngine()

        .capture()

    )

    image = screenshot.image

    if (

        len(image.shape) == 3

        and

        image.shape[2] == 4

    ):

        image = cv2.cvtColor(

            image,

            cv2.COLOR_BGRA2BGR

        )

    cv2.imwrite(

        "samples/real_screen.png",

        image

    )

    print()

    print(

        image.shape

    )

    print(

        image.min(),

        image.max()

    )