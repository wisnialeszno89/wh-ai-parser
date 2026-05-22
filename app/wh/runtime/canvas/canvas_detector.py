from app.wh.runtime.canvas.canvas_bounds import (
    CanvasBounds
)


class CanvasDetector:

    def detect(self):

        print(
            "[CANVAS] detect bounds"
        )

        return CanvasBounds(

            x=100,

            y=100,

            width=800,

            height=800
        )