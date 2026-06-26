from PIL import ImageGrab
import numpy as np


class ScreenshotProvider:

    def capture(self):

        image = ImageGrab.grab()

        return np.array(image)