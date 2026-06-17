class KeyPress:

    def __init__(

        self,

        enabled=False

    ):

        self.enabled = enabled

    def enter(

        self

    ):

        if not self.enabled:

            print()

            print(

                "ENTER"

            )

            print(

                "SIMULATION"

            )

            return "enter"

        import pyautogui

        pyautogui.press(

            "enter"

        )

        return "enter"

    def press(

        self,

        key

    ):

        if not self.enabled:

            print()

            print(

                key.upper()

            )

            print(

                "SIMULATION"

            )

            return key

        import pyautogui

        pyautogui.press(

            key

        )

        return key