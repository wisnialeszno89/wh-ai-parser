import pyautogui


class KeyboardController:

    def write(
        self,
        text: str,
    ):

        print(f"[KEYBOARD] WRITE '{text}'")

        pyautogui.write(
            str(text),
            interval=0.02,
        )

    def press(
        self,
        key: str,
    ):

        print(f"[KEYBOARD] PRESS {key}")

        pyautogui.press(key)

    def hotkey(
        self,
        *keys,
    ):

        joined = " + ".join(keys)

        print(f"[KEYBOARD] HOTKEY {joined}")

        pyautogui.hotkey(*keys)