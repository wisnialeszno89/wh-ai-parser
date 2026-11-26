"""Read-only UI Automation identity check for the customer-picker control.

Never clicks, invokes, focuses or enumerates customer data. Prints bounded
structural properties only (no titles, HWNDs, runtime IDs, names or values).
Run while the document-properties dialog is still open.
"""
from __future__ import annotations

import os

TARGET_ID = "IDC_ZAMAWIAJACY"
PROPERTIES_TITLE = "Właściwości dokumentu"


def safe_control_properties(info) -> dict:
    """Allowlist boolean and coarse type metadata; never disclose UI data."""
    role = str(getattr(info, "control_type", "") or "").strip().casefold()
    if role not in {"button", "edit", "combobox", "pane", "custom", "text"}:
        role = "other"
    return {
        "role": role,
        "visible": getattr(info, "visible", None) is True,
        "enabled": getattr(info, "enabled", None) is True,
        "runtime_id_present": bool(getattr(info, "runtime_id", None)),
    }


def main() -> int:
    if os.name != "nt":
        print("PICKER_DIAGNOSTIC=windows_required")
        return 2
    try:
        from pywinauto import Desktop
        from app.agent.environment.windows_desktop_environment_adapter import (
            WindowsDesktopEnvironmentAdapter,
        )
        adapter = WindowsDesktopEnvironmentAdapter()
        foreground = adapter._capture_foreground_window()
        inventory = adapter._capture_visible_windows(
            foreground.handle, snapshot=foreground,
        )
        candidates = [
            w for w in inventory
            if (getattr(w, "application", "") or "")
            .replace("\\", "/").rsplit("/", 1)[-1].casefold() == "okna.exe"
            and getattr(w, "title", None) == PROPERTIES_TITLE
            and getattr(w, "is_visible", False) is True
            and getattr(w, "is_minimized", False) is False
        ]
        if len(candidates) != 1:
            print("PICKER_DIAGNOSTIC=properties_window_not_unique")
            print("PROPERTIES_WINDOW_COUNT=" + str(min(len(candidates), 9)))
            return 1
        root = Desktop(backend="uia").window(handle=candidates[0].handle)
        wrapper = root.wrapper_object()
        if wrapper.window_text() != PROPERTIES_TITLE:
            print("PICKER_DIAGNOSTIC=properties_window_changed")
            return 1
        from app.agent.perception.windowhub_ui_automation_provider import (
            WindowHubUIAutomationProvider,
        )
        provider = WindowHubUIAutomationProvider()
        descendants = tuple(wrapper.descendants(depth=6))[:400]
        rect = wrapper.rectangle()
        origin_x, origin_y = int(rect.left), int(rect.top)
        labels = provider._collect_label_candidates(
            descendants, origin_x, origin_y,
        )
        matches = []
        for child in descendants:
            try:
                info = child.element_info
                if str(getattr(info, "automation_id", "")) != TARGET_ID:
                    continue
                record = safe_control_properties(info)
                actual_name = (getattr(info, "name", None) or "").strip()
                semantic, semantic_source = provider._resolve_semantic_label(
                    item=child,
                    name=actual_name,
                    control_type="button",
                    rectangle=child.rectangle(),
                    origin_x=origin_x,
                    origin_y=origin_y,
                    label_candidates=labels,
                )
                record["name_matches_expected"] = (
                    actual_name == "Wybierz istniejącego klienta"
                )
                record["semantic_label_matches_expected"] = (
                    semantic == "Wybierz istniejącego klienta"
                )
                record["semantic_label_source"] = (
                    semantic_source if semantic_source in {
                        "uia_name", "uia_parent", "uia_text_neighbor",
                        "ambiguous_neighbor", "none"
                    } else "other"
                )
                matches.append(record)
                if len(matches) >= 10:
                    break
            except Exception:
                continue
        print("PICKER_DIAGNOSTIC=read_only")
        print("PROPERTIES_FOREGROUND=" + str(candidates[0].handle == foreground.handle))
        print("TARGET_ID_MATCH_COUNT=" + str(len(matches)))
        for i, match in enumerate(matches, 1):
            pre = "TARGET_" + str(i) + "_"
            for key, value in match.items():
                print(pre + key.upper() + "=" + str(value))
        print("NATIVE_INPUT=False")
        print("CUSTOMER_TEXT_EXPORTED=False")
        return 0
    except Exception as exc:
        print("PICKER_DIAGNOSTIC=unavailable")
        print("ERROR_TYPE=" + type(exc).__name__)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
