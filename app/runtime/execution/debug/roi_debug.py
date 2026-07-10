import os

import cv2


class ROIDebug:

    def __init__(self):

        self.counter = 1

        os.makedirs(
            "outputs/roi",
            exist_ok=True,
        )

    def save(
        self,
        roi,
    ):

        filename = (
            f"outputs/roi/{self.counter:04}.png"
        )

        cv2.imwrite(
            filename,
            roi,
        )

        print(
            f"[ROI] {filename}"
        )

        self.counter += 1