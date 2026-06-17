import numpy as np
import mss

from app.wh.vision.screenshot import (
    Screenshot
)


class MSSScreenshotEngine:

    def capture(

        self

    ):

        with mss.mss() as sct:

            monitor = (

                sct.monitors[1]

            )

            shot = (

                sct.grab(

                    monitor

                )

            )

            image = np.array(

                shot

            )

            return Screenshot(

                width=shot.width,

                height=shot.height,

                image=image

            )