from __future__ import annotations

import ctypes
from ctypes import wintypes
import json
import os
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _wait_for_window_foreground(window_handle: int, timeout_seconds: float = 45.0) -> bool:
    """Wait for the user to focus the target WindowHub window; never set focus."""
    if window_handle <= 0:
        return False

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    get_foreground = user32.GetForegroundWindow
    get_foreground.restype = wintypes.HWND
    get_ancestor = user32.GetAncestor
    get_ancestor.argtypes = (wintypes.HWND, wintypes.UINT)
    get_ancestor.restype = wintypes.HWND

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            foreground_handle = int(get_foreground() or 0)
            if foreground_handle == window_handle:
                return True
            # A modal/owned WindowHub dialog may be foreground while its root
            # owner remains the intended WindowHub top-level window.
            if foreground_handle > 0:
                root_owner_handle = int(
                    get_ancestor(wintypes.HWND(foreground_handle), 3) or 0
                )
                if root_owner_handle == window_handle:
                    return True
        except Exception:
            # Keep waiting if a transient Win32 query fails.
            pass
        time.sleep(0.25)
    return False


def main() -> int:
    """Run a read-only OCR/table observation on the already focused WindowHub."""
    if os.name != "nt":
        print("ABORTED: this diagnostic requires Windows.")
        return 2

    # Import Windows-specific repository modules only after the platform guard.
    from app.agent.environment.windowhub_environment_adapter import (
        WindowHubEnvironmentAdapter,
    )
    from app.agent.perception.windowhub_ocr_provider import WindowHubOCRProvider

    print("WindowHub OCR table inspection (READ ONLY)")
    print("==========================================")
    print("No focus changes, clicks, typing, or other GUI actions will be performed.")
    print()

    environment = WindowHubEnvironmentAdapter()
    try:
        observation = environment.observe()
    except Exception as exc:
        print(
            "ABORTED: could not capture WindowHub observation: "
            f"{type(exc).__name__}: {exc}"
        )
        return 3

    title = str(getattr(observation.state, "active_window_title", "") or "")
    focused = observation.metadata.get("window_focused") is True
    print(f"window_title={title!r}")
    print(f"window_focused={focused}")
    print(f"screenshot_source={observation.metadata.get('source')!r}")

    if not focused:
        if "OFR/" not in title.upper():
            print()
            print("ABORTED: the detected WindowHub title does not identify an OFR/ offer.")
            print("Open the intended offer table and rerun.")
            return 5

        window_handle = observation.metadata.get("window_handle")
        try:
            window_handle = int(window_handle)
        except (TypeError, ValueError):
            window_handle = 0

        print()
        print("WindowHub is not currently the foreground window.")
        print("Click the intended WindowHub offer now; waiting up to 45 seconds.")
        print("This tool will not activate or focus the window for you.")
        if not _wait_for_window_foreground(window_handle):
            print("ABORTED: WindowHub did not become the foreground window in time.")
            return 4

        # Capture a fresh frame after the user has focused the exact target HWND.
        try:
            observation = environment.observe()
        except Exception as exc:
            print(
                "ABORTED: could not recapture focused WindowHub: "
                f"{type(exc).__name__}: {exc}"
            )
            return 3

        title = str(getattr(observation.state, "active_window_title", "") or "")
        focused = observation.metadata.get("window_focused") is True
        print(f"window_title={title!r}")
        print(f"window_focused={focused}")
        if not focused:
            print("ABORTED: the fresh observation still does not confirm WindowHub focus.")
            return 4

    if "OFR/" not in title.upper():
        print()
        print("ABORTED: the active WindowHub title does not identify an OFR/ offer.")
        print("Open the intended offer table, keep it in the foreground, and rerun.")
        return 5

    try:
        elements = WindowHubOCRProvider().perceive(observation)
    except Exception as exc:
        print(
            f"ABORTED: OCR provider failed unexpectedly: "
            f"{type(exc).__name__}: {exc}"
        )
        return 6

    metadata = observation.metadata
    reconstruction = metadata.get("windowhub_ocr_table_reconstruction")
    payload = reconstruction.to_payload() if reconstruction is not None else None

    summary = {
        "window_title": title,
        "window_focused": focused,
        "ocr_status": metadata.get("windowhub_ocr_status"),
        "ocr_element_count": metadata.get("windowhub_ocr_element_count", len(elements)),
        "table_status": metadata.get("windowhub_ocr_table_status", "not_available"),
        "table_error_type": metadata.get("windowhub_ocr_table_error"),
        "table_row_count": metadata.get("windowhub_ocr_table_row_count", 0),
        "table_complete_row_count": metadata.get(
            "windowhub_ocr_table_complete_row_count", 0
        ),
        "table_field_refinement_count": metadata.get(
            "windowhub_ocr_table_field_refinement_count", 0
        ),
        "table_lp_refinement_count": metadata.get(
            "windowhub_ocr_table_lp_refinement_count", 0
        ),
        "table": payload,
        "safety_note": (
            "OCR-derived values are observations, not independently verified facts. "
            "This diagnostic does not execute GUI actions."
        ),
    }

    print()
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))

    if summary["ocr_status"] == "error":
        return 9
    if summary["table_status"] == "error":
        return 7
    if summary["table_row_count"] <= 0:
        return 8
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
