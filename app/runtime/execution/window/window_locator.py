from app.runtime.execution.window.window_rect import (
    WindowRect,
)

import pygetwindow as gw


class WindowLocator:

    def locate(
        self,
    ) -> WindowRect:

        candidates = []

        print()
        print("=" * 60)
        print("[WINDOW LOCATOR]")
        print("=" * 60)

        for window in gw.getAllWindows():

            try:

                title = (window.title or "").strip()

                print(
                    f"[RAW] "
                    f"title={title!r} "
                    f"class={window._hWnd}"
                )

                if not title:
                    continue

                print(
                    f"[TITLE] {title!r}"
                )

                #
                # Match every WindowHub window.
                #

                if "okna" not in title.lower():
                    continue

                print(
                    f"[MATCH] "
                    f"{window.left},"
                    f"{window.top} "
                    f"{window.width}x"
                    f"{window.height}"
                )

                #
                # Ignore minimized windows.
                #

                if (
                    window.left < -10000
                    or window.top < -10000
                ):

                    print(
                        "[SKIP] Minimized"
                    )

                    continue

                candidates.append(
                    window
                )

            except Exception as e:

                print()

                print(
                    "[WINDOW ERROR]"
                )

                print(
                    type(e).__name__
                )

                print(
                    e
                )

        print()

        print(
            f"[MATCHES] {len(candidates)}"
        )

        if not candidates:

            raise RuntimeError(
                "WindowHub window not found."
            )

        #
        # Largest window wins.
        #

        window = max(

            candidates,

            key=lambda w: (
                w.width * w.height
            ),

        )

        print()
        print("=" * 60)
        print("[WINDOW SELECTED]")
        print("=" * 60)

        print(
            window.title
        )

        print(
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