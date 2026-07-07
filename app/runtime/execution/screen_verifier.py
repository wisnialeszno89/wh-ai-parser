import cv2

from app.runtime.execution.vision.runtime_vision import (
    RuntimeVision,
)


class ScreenVerifier:

    def __init__(self):

        self.vision = RuntimeVision()

    def verify_change(
        self,
        previous,
    ) -> bool:

        current = self.vision.capture()

        difference = cv2.absdiff(

            previous.image,

            current.image,

        )

        changed = difference.sum() > 0

        print(
            f"[VERIFY] changed={changed}"
        )

        return changed