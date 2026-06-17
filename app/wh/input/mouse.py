import os


class Mouse:

    def __init__(

        self,

        enabled=False

    ):

        self.enabled = enabled

    def click(

        self,

        x,

        y

    ):

        print()

        print(

            f"MOVE TO ({x}, {y})"

        )

        if (

            self.enabled

            and

            "DISPLAY" in os.environ

        ):

            import pyautogui

            pyautogui.moveTo(

                x,

                y,

                duration=1

            )

        else:

            print(

                "SIMULATION"

            )

        return (

            x,

            y

        )