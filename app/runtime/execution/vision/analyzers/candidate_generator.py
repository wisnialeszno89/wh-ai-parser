import cv2

from app.runtime.execution.vision.models.control_role import (
    ControlRole,
)

from app.runtime.execution.vision.models.control_state import (
    ControlState,
)

from app.runtime.execution.vision.models.control_type import (
    ControlType,
)

from app.runtime.execution.vision.models.gui_object import (
    GUIObject,
)

from app.runtime.execution.vision.models.rect import (
    Rect,
)

from app.wh.vision.screenshot import (
    Screenshot,
)


class CandidateGenerator:
    """
    Generates candidate GUI objects.

    This class DOES NOT classify controls.

    It only answers:

        "Something interesting is here."
    """

    def analyze(
        self,
        screenshot: Screenshot,
        section: GUIObject,
    ) -> None:

        image = screenshot.image

        r = section.bounds

        roi = image[
            r.top:r.bottom,
            r.left:r.right,
        ]

        #
        # STEP 1
        #

        gray = cv2.cvtColor(
            roi,
            cv2.COLOR_BGR2GRAY,
        )

        #
        # STEP 2
        #

        blur = cv2.GaussianBlur(
            gray,
            (5, 5),
            0,
        )

        #
        # STEP 3
        #

        binary = cv2.adaptiveThreshold(

            blur,

            255,

            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,

            cv2.THRESH_BINARY_INV,

            15,

            3,

        )

        #
        # DEBUG
        #

        cv2.imwrite(
        f"outputs/debug/{section.id}_threshold.png",
        binary,
        )

        #
        # No candidates yet.
        #

        section.children.clear()