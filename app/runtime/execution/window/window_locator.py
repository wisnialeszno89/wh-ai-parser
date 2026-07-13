from app.runtime.execution.window.window_rect import (
    WindowRect,
)

import pygetwindow as gw


class WindowLocator:

    def locate(
        self,
    ) -> WindowRect:

        candidates = []

        for window in gw.getAllWindows():

            try:

                if not window.title:
                    continue

                if not window.title.startswith("Okna"):
                    continue

                #
                # Ignore minimized/hidden windows.
                #

                if (
                    window.width < 500
                    or window.height < 500
                    or window.left < -10000
                    or window.top < -10000
                ):
                    continue

                candidates.append(window)

            except Exception:
                pass

        if not candidates:

            raise RuntimeError(
                "WindowHub window not found."
            )

        #
        # Use the largest visible window.
        #

        window = max(
            candidates,
            key=lambda w: w.width * w.height,
        )

        print()
        print(f"[WINDOW] {window.title}")
        print(
            f"[RECT] "
            f"{window.left},"
            f"{window.top} "
            f"{window.width}x"
            f"{window.height}"
        )

        return WindowRect(
            left=window.left,
            top=window.top,
            width=window.width,
            height=window.height,
        )