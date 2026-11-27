"""Read-only inventory of visible WindowHub windows after uncertain picker click.

No focus changes, screenshots, UIA interactions, client titles, handles or
credentials are exported. Only classified stages and owner relationships.
"""
from __future__ import annotations

import os

from app.agent.runtime.navimind_background_windowhub_reader import (
    _is_windowhub,
    safe_stage,
)


def safe_window_summary(inventory, *, foreground_handle: int | None = None) -> list[dict]:
    windows = [w for w in inventory if _is_windowhub(w)]
    # No unbounded window enumeration in the output.
    windows = windows[:8]
    result = []
    for index, window in enumerate(windows, start=1):
        owner = getattr(window, "root_owner_handle", None)
        result.append({
            "index": index,
            "stage": safe_stage(getattr(window, "title", None)),
            "foreground": bool(
                getattr(window, "is_foreground", False)
                or window.handle == foreground_handle
            ),
            "same_root_owner_as_first": bool(
                index > 1
                and type(owner) is int and owner > 0
                and owner == getattr(windows[0], "root_owner_handle", None)
            ),
        })
    return result


def main() -> int:
    if os.name != "nt":
        print("WINDOWHUB_DIAGNOSTIC=windows_required")
        return 2
    from app.agent.environment.windows_desktop_environment_adapter import (
        WindowsDesktopEnvironmentAdapter,
    )
    try:
        adapter = WindowsDesktopEnvironmentAdapter()
        foreground = adapter._capture_foreground_window()
        inventory = adapter._capture_visible_windows(
            foreground.handle, snapshot=foreground,
        )
        summaries = safe_window_summary(
            inventory, foreground_handle=foreground.handle,
        )
    except Exception as exc:
        print("WINDOWHUB_DIAGNOSTIC=unavailable")
        print("ERROR_TYPE=" + type(exc).__name__)
        return 1
    print("WINDOWHUB_DIAGNOSTIC=read_only")
    print("WINDOWHUB_WINDOW_COUNT=" + str(len(summaries)))
    for item in summaries:
        prefix = "WINDOW_" + str(item["index"]) + "_"
        print(prefix + "STAGE=" + item["stage"])
        print(prefix + "FOREGROUND=" + str(item["foreground"]))
        if item["index"] > 1:
            print(prefix + "SAME_ROOT_OWNER_AS_FIRST=" +
                  str(item["same_root_owner_as_first"]))
    print("NATIVE_INPUT=False")
    print("SCREENSHOT_CAPTURED=False")
    print("CUSTOMER_VALUES_EXPORTED=False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
