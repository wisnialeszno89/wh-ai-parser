"""Select an exact catalog entry inside the owned WindowHub hardware dialog."""
from __future__ import annotations

import json
import re
import time

from app.agent.knowledge.whokna_offer_guide import standard_tilt_turn_labels


def normalize_hardware_label(name):
    return " ".join((name or "").strip().casefold().split())


def choose_ur_option(items):
    """Resolve the specified standard among currently observed catalog entries."""
    allowed = {normalize_hardware_label(label) for label in standard_tilt_turn_labels()}
    exact = [item for item in items if normalize_hardware_label(item[0]) in allowed]
    return exact[0] if len(exact) == 1 else None


def report_catalogue_candidates(rows):
    labels = sorted({
        name for label, *_ in rows
        if re.match(r"ur(?:\s|[-0-9])", name := normalize_hardware_label(label))
    })
    print("WH_HARDWARE_UR_CANDIDATES=" + json.dumps(labels[:12], ensure_ascii=False), flush=True)


def read_native_rows(dialog):
    trees = [w for w in dialog.descendants(class_name="SysTreeView32") if w.is_visible() and w.is_enabled()]
    if len(trees) != 1:
        return []

    tree = trees[0]
    stack = [(item, (index,)) for index, item in enumerate(tree.roots())]
    rows = []
    # Bound inspection even in large maker catalogs.
    for _ in range(400):
        if not stack:
            return rows
        item, path = stack.pop()
        rows.append((item.text(), path, tree))
        if len(path) < 8 and item.is_expanded():
            stack.extend((child, (*path, index)) for index, child in enumerate(item.children()))
    return [] if stack else rows


def read_uia_rows(dialog):
    rows = []
    for item in dialog.descendants(control_type="TreeItem"):
        try:
            info = item.element_info
            if info.visible and info.enabled:
                rows.append((str(info.name or ""), item.iface_selection_item))
        except Exception:
            continue
    return rows


def choose_and_confirm_ur(hwnd, *, still_owned, confirm):
    """Read the live catalog, choose once, and read back the exact selection."""
    from pywinauto import Desktop

    if not still_owned():
        return False
    native_dialog = None
    try:
        native_dialog = Desktop(backend="win32").window(handle=hwnd).wrapper_object()
        native_rows = read_native_rows(native_dialog)
    except (OSError, RuntimeError, ValueError, AttributeError):
        native_rows = []

    print(f"WH_HARDWARE_NATIVE_ROWS={len(native_rows)}", flush=True)
    if native_rows:
        target = choose_ur_option(native_rows)
        if target is None or not still_owned():
            print("WH_HARDWARE_EVIDENCE=exact_standard_not_unique_in_native_catalogue", flush=True)
            report_catalogue_candidates(native_rows)
            return False
        label, path, tree = target

        def selected():
            item = tree.get_item(path)
            return (
                normalize_hardware_label(item.text()) == normalize_hardware_label(label)
                and tree.is_selected(path)
            )

        if not selected():
            if not still_owned() or normalize_hardware_label(tree.get_item(path).text()) != normalize_hardware_label(label):
                return False
            tree.select(path)
        source = "win32_tree"
    else:
        dialog = Desktop(backend="uia").window(handle=hwnd).wrapper_object()
        rows = read_uia_rows(dialog)
        target = choose_ur_option(rows)
        if target is None or not still_owned():
            print("WH_HARDWARE_EVIDENCE=exact_standard_not_unique_in_uia_catalogue", flush=True)
            report_catalogue_candidates(rows)
            return False
        label, selection = target

        def selected():
            match = choose_ur_option(read_uia_rows(dialog))
            return bool(match and normalize_hardware_label(match[0]) == normalize_hardware_label(label)
                        and match[1].CurrentIsSelected)

        if not selected():
            if not still_owned():
                return False
            selection.Select()
        source = "uia_tree"

    for attempt in range(5):
        if not still_owned():
            return False
        if selected():
            print(f"WH_HARDWARE_SELECTED={label}", flush=True)
            print("WH_HARDWARE_EVIDENCE=verified_" + source, flush=True)
            return confirm_selected_hardware(native_dialog, still_owned, confirm)
        if attempt < 4:
            time.sleep(0.25)
    print("WH_HARDWARE_EVIDENCE=selection_readback_unverified", flush=True)
    return False


def confirm_selected_hardware(dialog, still_owned, confirm):
    """Use the native IDOK when available, otherwise the existing UIA path."""
    if dialog is not None:
        try:
            buttons = [
                w for w in dialog.descendants(class_name="Button")
                if w.control_id() == 1 and w.window_text().strip().replace("&", "").casefold() == "ok"
                and w.is_visible() and w.is_enabled()
            ]
        except (OSError, RuntimeError, ValueError, AttributeError):
            buttons = []
        if len(buttons) > 1:
            return False
        if buttons:
            if not still_owned():
                return False
            buttons[0].click()
            return True
    return still_owned() and confirm()
