import pyautogui


class KeyboardController:

    def write(
        self,
        text: str,
    ):
        value = str(text)

        print(f"[KEYBOARD] WRITE '{value}'")

        if value.isascii():
            pyautogui.write(
                value,
                interval=0.02,
            )
            return

        if __import__("os").name != "nt":
            raise RuntimeError(
                "Unicode text entry requires Windows."
            )

        self._paste_unicode_windows(value)

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

    @staticmethod
    def _paste_unicode_windows(value: str) -> None:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        CF_UNICODETEXT = 13
        GMEM_MOVEABLE = 0x0002

        encoded = (value + "\\x00").encode("utf-16-le")

        handle = kernel32.GlobalAlloc(
            GMEM_MOVEABLE,
            len(encoded),
        )

        if not handle:
            raise RuntimeError(
                "GlobalAlloc failed for Unicode clipboard text."
            )

        try:
            pointer = kernel32.GlobalLock(handle)
            if not pointer:
                raise RuntimeError(
                    "GlobalLock failed for Unicode clipboard text."
                )

            try:
                ctypes.memmove(
                    pointer,
                    encoded,
                    len(encoded),
                )
            finally:
                kernel32.GlobalUnlock(handle)

            if not user32.OpenClipboard(None):
                raise RuntimeError(
                    "OpenClipboard failed."
                )

            try:
                if not user32.EmptyClipboard():
                    raise RuntimeError(
                        "EmptyClipboard failed."
                    )

                if not user32.SetClipboardData(
                    CF_UNICODETEXT,
                    handle,
                ):
                    raise RuntimeError(
                        "SetClipboardData failed."
                    )

                # Ownership transfers to the clipboard after a successful
                # SetClipboardData call.
                handle = None
            finally:
                user32.CloseClipboard()
        finally:
            if handle:
                kernel32.GlobalFree(handle)

        pyautogui.hotkey("ctrl", "v")
