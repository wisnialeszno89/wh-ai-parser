from PIL import ImageGrab
import numpy as np
import os


class ScreenshotProvider:

    def capture(self):

        #
        # Codespaces / Linux bez GUI
        #

        if "DISPLAY" not in os.environ:

            raise RuntimeError(
                "ScreenshotProvider requires a graphical desktop. "
                "Run Vision locally on Windows."
            )

        image = ImageGrab.grab()

        return np.array(image)