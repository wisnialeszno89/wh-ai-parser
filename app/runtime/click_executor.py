import time

from app.runtime.execution.mouse_controller import (
    MouseController,
)


class ClickExecutor:

    def __init__(self):

        self.mouse = MouseController()

    def execute(
        self,
        element,
    ):

        click_x = (
            element.x
            + element.width // 2
        )

        click_y = (
            element.y
            + element.height // 2
        )

        print(
            f"[CENTER] ({click_x}, {click_y})"
        )

        print(
            f"[CONFIDENCE] {element.confidence:.3f}"
        )

        print()

        print(
            "[DEBUG] Clicking in 2 seconds..."
        )

        time.sleep(2)

        self.mouse.click(
            click_x,
            click_y,
        )