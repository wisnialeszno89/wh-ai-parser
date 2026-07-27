import time

from app.runtime.execution.mouse_controller import (
    MouseController,
)


class ClickExecutor:

    def __init__(self):

        self.mouse = MouseController()

    #
    # Click UI element.
    #

    def execute(
        self,
        element,
    ):

        self.click_xy(

            element.x + element.width // 2,

            element.y + element.height // 2,

            confidence=element.confidence,

        )

    #
    # Click arbitrary point.
    #

    def click_xy(
        self,
        x: int,
        y: int,
        confidence: float | None = None,
    ):

        print()

        print(
            f"[CLICK] ({x}, {y})"
        )

        if confidence is not None:

            print(
                f"[CONFIDENCE] {confidence:.3f}"
            )

        print()

        print(
            "[DEBUG] Clicking in 2 seconds..."
        )

        time.sleep(2)

        self.mouse.click(
            x,
            y,
        )

    #
    # Double click.
    #

    def double_click_xy(
        self,
        x: int,
        y: int,
    ):

        self.click_xy(
            x,
            y,
        )

        self.click_xy(
            x,
            y,
        )