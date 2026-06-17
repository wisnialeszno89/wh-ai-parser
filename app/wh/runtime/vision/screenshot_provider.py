import numpy as np


class ScreenshotProvider:

    def capture(

        self

    ):

        return self._capture()

    def _capture(

        self

    ):

        return np.zeros(

            (

                1080,

                1920,

                3

            ),

            dtype=np.uint8

        )