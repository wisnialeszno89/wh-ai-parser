from __future__ import annotations

import sys


def ensure_windows_sta() -> None:
    """
    Ensure Python's COM initialization hint requests STA before
    pywinauto/comtypes is imported.

    pywinauto + UI Automation is most reliable when COM is initialized
    in the single-threaded apartment.
    """

    if sys.platform != "win32":
        return

    if getattr(sys, "coinit_flags", None) != 2:
        sys.coinit_flags = 2
