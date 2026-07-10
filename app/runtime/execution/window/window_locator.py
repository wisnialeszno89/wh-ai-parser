from app.runtime.execution.window.window_rect import (
    WindowRect,
)

import pygetwindow as gw


class WindowLocator:

    def locate(
        self,
    ) -> WindowRect:

        for window in gw.getAllWindows():

            try:

                if not window.title:

                    continue

                #
                # Główne okno edycji WindowHub.
                #

                if not window.title.startswith(
                    "Okna"
                ):

                    continue

                print()

                print(
                    f"[WINDOW] {window.title}"
                )

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

            except Exception:

                pass

        raise RuntimeError(

            "WindowHub window not found."

        )