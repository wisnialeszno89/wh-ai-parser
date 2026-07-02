class MouseController:

    def click(
        self,
        x: int,
        y: int,
    ):

        import pyautogui

        print(
            f"[CLICK] ({x}, {y})"
        )

        pyautogui.click(
            x,
            y,
        )