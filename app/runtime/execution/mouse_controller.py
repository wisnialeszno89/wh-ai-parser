import pyautogui


class MouseController:

    def click(
        self,
        x: int,
        y: int,
    ):

        print(f"[CLICK] ({x}, {y})")

        pyautogui.click(x, y)