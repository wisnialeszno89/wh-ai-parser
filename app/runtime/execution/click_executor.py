import time

from app.runtime.execution.mouse_controller import (
    MouseController,
)


class ClickExecutor:

    def __init__(self):

        self.mouse = MouseController()

    #
    # Click UI element whose coordinates originate from a WindowHub
    # screenshot. The origin converts local vision coordinates into
    # absolute desktop coordinates used by pyautogui.
    #

    def execute(
        self,
        element,
        origin: tuple[int, int] = (0, 0),
    ):

        self.click_xy(

            element.x + element.width // 2,

            element.y + element.height // 2,

            confidence=element.confidence,

            origin=origin,

        )

    #
    # Click arbitrary point in WindowHub screenshot coordinates.
    #

    def click_xy(
        self,
        x: int,
        y: int,
        confidence: float | None = None,
        origin: tuple[int, int] = (0, 0),
    ):

        screen_x = x + origin[0]
        screen_y = y + origin[1]

        print()

        print(
            f"[CLICK] local=({x}, {y}) "
            f"screen=({screen_x}, {screen_y})"
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
            screen_x,
            screen_y,
        )

    #
    # Double click.
    #

    def double_click_xy(
        self,
        x: int,
        y: int,
        origin: tuple[int, int] = (0, 0),
    ):

        self.click_xy(
            x,
            y,
            origin=origin,
        )

        self.click_xy(
            x,
            y,
            origin=origin,
        )