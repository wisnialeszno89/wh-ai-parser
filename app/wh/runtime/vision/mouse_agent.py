class MouseAgent:

    def click(

        self,

        point

    ):

        try:

            import pyautogui

            pyautogui.click(

                point.x,

                point.y

            )

        except Exception:

            pass

        return True