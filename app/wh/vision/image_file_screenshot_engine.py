import cv2

from app.wh.vision.screenshot import (
    Screenshot
)


class ImageFileScreenshotEngine:

    def capture(

        self,

        path

    ):

        image = cv2.imread(

            path

        )

        height, width = (

            image.shape[:2]

        )

        return Screenshot(

            width=width,

            height=height,

            image=image

        )