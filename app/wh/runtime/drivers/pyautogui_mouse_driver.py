import pyautogui

from app.wh.runtime.drivers.base_mouse_driver import (
    BaseMouseDriver
)


class PyAutoGuiMouseDriver(
    BaseMouseDriver
):

    def move(

        self,
        x,
        y
    ):

        print(
            f"[REAL MOUSE] move "
            f"({x}, {y})"
        )

        pyautogui.moveTo(
            x,
            y,
            duration=0.1
        )

    def click(

        self,
        x,
        y
    ):

        print(
            f"[REAL MOUSE] click "
            f"({x}, {y})"
        )

        pyautogui.click(
            x,
            y
        )