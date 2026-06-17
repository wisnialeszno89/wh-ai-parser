import numpy as np

from app.wh.vision.screenshot import (
    Screenshot
)


class FakeScreenshotEngine:

    def capture(

        self

    ):

        image = np.zeros(

            (

                1080,

                1920,

                3

            ),

            dtype=np.uint8

        )

        return Screenshot(

            width=1920,

            height=1080,

            image=image

        )