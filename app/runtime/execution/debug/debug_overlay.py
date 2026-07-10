from pathlib import Path

import cv2

from app.runtime.execution.vision.models.gui_object import GUIObject


class DebugOverlay:
    """
    Draws diagnostic overlays on screenshots.

    Used only for development and debugging.
    """

    OUTPUT_DIR = Path("outputs/debug")

    def __init__(self):

        self.OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.counter = 0

    def render(
        self,
        screenshot,
        toolbar: GUIObject,
    ):

        image = screenshot.image.copy()

        #
        # Toolbar
        #

        rect = toolbar.bounds

        cv2.rectangle(

            image,

            (rect.left, rect.top),

            (rect.right, rect.bottom),

            (0, 255, 0),

            2,

        )
                #
        # Controls
        #

        for section in toolbar.children:

            for control in section.children:

                r = control.bounds

                cv2.rectangle(

                    image,

                    (r.left, r.top),

                    (r.right, r.bottom),

                    (0, 0, 255),

                    2,

                )

                cv2.putText(

                    image,

                    control.id,

                    (r.left, r.bottom + 18),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.45,

                    (0, 0, 255),

                    1,

                )
                
        cv2.putText(

            image,

            "Toolbar",

            (rect.left + 5, rect.top + 25),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.7,

            (0, 255, 0),

            2,

        )

        #
        # Sections
        #

        for section in toolbar.children:

            r = section.bounds

            cv2.rectangle(

                image,

                (r.left, r.top),

                (r.right, r.bottom),

                (255, 0, 0),

                2,

            )

            cv2.putText(

                image,

                section.id,

                (r.left + 5, r.top + 60),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.6,

                (255, 0, 0),

                2,

            )

        self.counter += 1

        filename = self.OUTPUT_DIR / f"{self.counter:04d}.png"

        cv2.imwrite(

            str(filename),

            image,

        )

        print(f"[DEBUG] Saved {filename}")