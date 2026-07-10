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


class ControlDetector:
    """
    Detects potential GUI controls inside a toolbar section.

    MVP version.

    Later this detector will use:
    - morphology
    - contour filtering
    - OCR
    - template validation
    """

    MIN_WIDTH = 12
    MIN_HEIGHT = 12

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

        gray = cv2.cvtColor(
            roi,
            cv2.COLOR_BGR2GRAY,
        )

        edges = cv2.Canny(
            gray,
            60,
            150,
        )

        contours, _ = cv2.findContours(
            edges,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        section.children.clear()

        counter = 1

        for contour in contours:

            x, y, w, h = cv2.boundingRect(
                contour,
            )

            if w < self.MIN_WIDTH:
                continue

            if h < self.MIN_HEIGHT:
                continue

            control = GUIObject(

                id=f"{section.id}_control_{counter}",

                type=ControlType.BUTTON,

                role=ControlRole.UNKNOWN,

                state=ControlState.VISIBLE,

                bounds=Rect(

                    x=r.left + x,

                    y=r.top + y,

                    width=w,

                    height=h,

                ),

            )

            section.add_child(
                control,
            )

            counter += 1