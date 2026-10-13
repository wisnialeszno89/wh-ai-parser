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


def _format_hwnd(value: int) -> str:
    """Format a Windows handle for unambiguous diagnostic output."""
    return f"0x{value:X}" if value > 0 else "0x0"


def _window_title(user32: object, window_handle: int) -> str:
    """Read a window title for diagnostics without changing window state."""
    if window_handle <= 0:
        return ""
    try:
        get_length = user32.GetWindowTextLengthW
        get_length.argtypes = (wintypes.HWND,)
        get_length.restype = ctypes.c_int
        get_text = user32.GetWindowTextW
        get_text.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
        get_text.restype = ctypes.c_int
        length = max(0, int(get_length(wintypes.HWND(window_handle))))
        buffer = ctypes.create_unicode_buffer(min(length + 1, 2048))
        get_text(wintypes.HWND(window_handle), buffer, len(buffer))
        return buffer.value
    except Exception as exc:
        return f"<title read failed: {type(exc).__name__}: {exc}>"


def _foreground_snapshot(user32: object) -> tuple[int, int, str]:
    """Return foreground HWND, root-owner HWND and foreground title."""
    get_foreground = user32.GetForegroundWindow
    get_foreground.restype = wintypes.HWND
    get_ancestor = user32.GetAncestor
    get_ancestor.argtypes = (wintypes.HWND, wintypes.UINT)
    get_ancestor.restype = wintypes.HWND
    foreground_handle = int(get_foreground() or 0)
    root_owner_handle = (
        int(get_ancestor(wintypes.HWND(foreground_handle), 3) or 0)
        if foreground_handle > 0
        else 0
    )
    return (
        foreground_handle,
        root_owner_handle,
        _window_title(user32, foreground_handle),
    )


def _wait_for_window_foreground(window_handle: int, timeout_seconds: float = 45.0) -> bool:
    """Wait for the user to focus the target WindowHub window; never set focus."""
    if window_handle <= 0:
        print("[FOCUS] Target WindowHub HWND is missing or invalid.")
        return False

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    from app.agent.environment.window_focus import is_target_window_focused

    deadline = time.monotonic() + timeout_seconds
    next_report = time.monotonic()
    last_snapshot = (0, 0, "")
    last_error = None
    while time.monotonic() < deadline:
        try:
            last_snapshot = _foreground_snapshot(user32)
            foreground_handle, root_owner_handle, _ = last_snapshot
            if is_target_window_focused(
                window_handle, foreground_handle, root_owner_handle
            ):
                print(
                    "[FOCUS] Confirmed target: "
                    f"target={_format_hwnd(window_handle)}, "
                    f"foreground={_format_hwnd(foreground_handle)}, "
                    f"root_owner={_format_hwnd(root_owner_handle)}, "
                    f"title={last_snapshot[2]!r}"
                )
                return True
            last_error = None
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"

        now = time.monotonic()
        if now >= next_report:
            print(
                "[FOCUS] Waiting: "
                f"target={_format_hwnd(window_handle)}, "
                f"foreground={_format_hwnd(last_snapshot[0])}, "
                f"root_owner={_format_hwnd(last_snapshot[1])}, "
                f"title={last_snapshot[2]!r}"
                + (f", win32_error={last_error}" if last_error else "")
            )
            next_report = now + 5.0
        time.sleep(0.25)

    print(
        "[FOCUS] Timeout snapshot: "
        f"target={_format_hwnd(window_handle)}, "
        f"foreground={_format_hwnd(last_snapshot[0])}, "
        f"root_owner={_format_hwnd(last_snapshot[1])}, "
        f"title={last_snapshot[2]!r}"
        + (f", win32_error={last_error}" if last_error else "")
    )
    return False



def _classify_table_region_detections(elements: object) -> dict[str, list[dict[str, object]]]:
    """Keep raw OCR observations for each relevant OFR table column."""
    detections: list[dict[str, object]] = []
    for element in elements:
        try:
            x = int(element.x)
            y = int(element.y)
            width = int(element.width)
            height = int(element.height)
            confidence = float(element.confidence)
            center_y = y + height / 2
        except (AttributeError, TypeError, ValueError):
            continue

        in_table_columns = (
            90 <= x < 600
            or 1090 <= x < 1260
        )
        if not in_table_columns or not 190 <= center_y <= 370:
            continue
        detections.append({
            "text": str(element.label),
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "confidence": round(confidence, 4),
        })

    return {
        "table_region_ocr_detections": detections,
        "lp_column_ocr_detections": [
            item for item in detections if 90 <= item["x"] < 180
        ],
        "quantity_article_ocr_detections": [
            item for item in detections if 185 <= item["x"] < 380
        ],
        "net_total_ocr_detections": [
            item for item in detections if 380 <= item["x"] < 500
        ],
        "unit_value_ocr_detections": [
            item for item in detections if 500 <= item["x"] < 600
        ],
        "dimensions_ocr_detections": [
            item for item in detections if 1090 <= item["x"] < 1260
        ],
    }


def _configure_console_output(streams=None) -> None:
    """Avoid crashes when PowerShell pipes native output through a legacy code page."""
    targets = streams if streams is not None else (sys.stdout, sys.stderr)
    for stream in targets:
        reconfigure = getattr(stream, "reconfigure", None)
        if not callable(reconfigure):
            continue
        try:
            reconfigure(errors="backslashreplace")
        except (OSError, ValueError):
            # Keep diagnostics best-effort when the stream disallows reconfiguration.
            continue


def main() -> int:
    """Run a read-only OCR/table observation on the already focused WindowHub."""
    _configure_console_output()
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
    for key in (
        "window_handle",
        "foreground_window_handle",
        "foreground_root_owner_handle",
    ):
        value = observation.metadata.get(key)
        try:
            value = int(value)
        except (TypeError, ValueError):
            value = 0
        print(f"{key}={_format_hwnd(value)}")
    try:
        initial_user32 = ctypes.WinDLL("user32", use_last_error=True)
        foreground_handle, root_owner_handle, foreground_title = _foreground_snapshot(
            initial_user32
        )
        print(f"foreground_window_title={foreground_title!r}")
        print(f"foreground_hwnd_verified={_format_hwnd(foreground_handle)}")
        print(f"foreground_root_owner_verified={_format_hwnd(root_owner_handle)}")
    except Exception as exc:
        print(f"foreground_diagnostics_error={type(exc).__name__}: {exc}")

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

    # Coordinates/confidence are observations for diagnosis, not actions.
    table_detections = _classify_table_region_detections(elements)

    summary = {
        "window_title": title,
        "window_focused": focused,
        "ocr_status": metadata.get("windowhub_ocr_status"),
        **table_detections,
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
