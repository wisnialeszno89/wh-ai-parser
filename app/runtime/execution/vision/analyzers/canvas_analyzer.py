from app.runtime.execution.vision.models.canvas import Canvas
from app.runtime.execution.vision.models.rect import Rect


class CanvasAnalyzer:

    def analyze(
        self,
        context,
    ):

        screenshot = context.screenshot

        toolbar = context.toolbar

        if toolbar is None:
            return context

        toolbar_bottom = toolbar.bounds.bottom

        width = screenshot.width
        height = screenshot.height

        #
        # Pierwsza heurystyka.
        #

        left = int(width * 0.18)
        right = int(width * 0.73)

        top = toolbar_bottom + 8
        bottom = int(height * 0.83)

        context.canvas = Canvas(

            bounds=Rect(
                x=left,
                y=top,
                width=right - left,
                height=bottom - top,
            )

        )

        print(
            f"[CANVAS] "
            f"{left},{top} "
            f"{right-left}x{bottom-top}"
        )

        return context