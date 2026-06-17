class Keyboard:

    def __init__(

        self,

        enabled=False

    ):

        self.enabled = enabled

    def write(

        self,

        text

    ):

        if self.enabled:

            import pyautogui

            pyautogui.write(

                text

            )

        return text