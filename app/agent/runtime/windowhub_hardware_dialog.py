"""Select a catalog UR option from the owned foreground hardware dialog."""
from __future__ import annotations

import re


def normalize_hardware_label(name):
    return " ".join((name or "").strip().casefold().split())


def choose_ur_option(items):
    """Prefer WindowHub's selected compatible UR item, then one unambiguous option."""
    candidates = [item for item in items if re.match(r"ur(?=\s|[-0-9])", normalize_hardware_label(item[0]))]
    selected = [item for item in candidates if item[1]]
    if len(selected) == 1:
        return selected[0]
    if selected:
        return None
    standard = [item for item in candidates if re.match(
        r"(?:ur activpilot(?:\s|$)|ur 1\+t\+\s*dfe$)", normalize_hardware_label(item[0]),
    )]
    if len(standard) == 1:
        return standard[0]
    return candidates[0] if len(candidates) == 1 else None


def choose_and_confirm_ur(hwnd, *, still_owned, confirm):
    """Use native UIA identities and read back the selection before accepting."""
    from pywinauto import Desktop

    def visible_rows():
        dialog = Desktop(backend="uia").window(handle=hwnd).wrapper_object()
        rows = []
        for item in dialog.descendants(control_type="TreeItem"):
            try:
                info = item.element_info
                if info.visible and info.enabled:
                    selection = item.iface_selection_item
                    rows.append((str(info.name or ""), bool(selection.CurrentIsSelected), selection))
            except Exception:
                continue
        return rows

    if not still_owned():
        return False
    target = choose_ur_option(visible_rows())
    if target is None or not still_owned():
        return False
    name, selected, selection = target
    if not selected:
        selection.Select()
    if not still_owned():
        return False
    verified = [row for row in visible_rows() if row[1] and normalize_hardware_label(row[0]) == normalize_hardware_label(name)]
    return len(verified) == 1 and still_owned() and confirm()
