import cv2

from app.runtime.execution.screen_verification import ScreenVerification

from app.runtime.execution.vision.runtime_vision import (
    RuntimeVision,
)


class ScreenVerifier:

    def __init__(self):

        self.vision = RuntimeVision()

    def verify_change(
        self,
        previous,
    ) -> ScreenVerification:

        current = self.vision.capture()

        print()
        print("=" * 60)
        print("[VERIFY]")

        print(
            "PREVIOUS:",
            previous.screenshot.image.shape,
        )

        print(
            "CURRENT :",
            current.screenshot.image.shape,
        )

        print("=" * 60)

        difference = cv2.absdiff(

            previous.screenshot.image,

            current.screenshot.image,

        )

        difference_score = int(
            difference.sum()
        )

        changed = difference_score > 0

        print(
            f"[VERIFY] changed={changed}"
        )

        print(
            f"[VERIFY] difference={difference_score}"
        )

        return ScreenVerification(

            changed=changed,

            difference_score=difference_score,

)