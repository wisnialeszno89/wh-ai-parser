import mss
import numpy as np

from app.runtime.execution.window.window_rect import (
    WindowRect,
)

from app.wh.vision.screenshot import (
    Screenshot,
)


class MSSScreenshotEngine:
    """
    Captures screenshots of a given window or screen region.

    This class is intentionally unaware of how the window
    was located. It only knows how to capture pixels.
    """

    def capture(
        self,
        rect: WindowRect,
    ) -> Screenshot:

        print(
            f"[SCREENSHOT] "
            f"{rect.left},{rect.top} "
            f"{rect.width}x{rect.height}"
        )

        with mss.mss() as sct:

            monitor = {
                "left": rect.left,
                "top": rect.top,
                "width": rect.width,
                "height": rect.height,
            }

            shot = sct.grab(monitor)

            image = np.array(shot)

            screenshot = Screenshot(
                width=shot.width,
                height=shot.height,
                image=image,
            )

        print(
            f"[SCREENSHOT] Captured "
            f"{screenshot.width}x{screenshot.height}"
        )

        return screenshot