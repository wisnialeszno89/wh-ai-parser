"""Real exact-customer lookup input for the WindowHub document dialog.

The lookup can be a DevExpress button without a selectable UIA row. Use
an editable child/search field when uniquely identified; otherwise send one
bounded type-ahead search to the *focused* verified IDC_ZAMAWIAJACY control.
Never send Enter or select the first result. Caller verifies actual customer.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CustomerSearchDecision:
    status: str
    reason: str
    search_control_count: int = 0
    selected_index: int | None = None


def classify_customer_search_controls(controls, *, picker_focused: bool) -> CustomerSearchDecision:
    """Choose one provable search edit, never a random document field.

    Prefer one edit structurally inside the customer lookup. If that yields
    several candidates, a uniquely focused edit inside the same lookup is
    enough to resolve the ambiguity. Focus outside the lookup is insufficient.
    """
    usable = [
        (index, control) for index, control in enumerate(controls)
        if control.get("role") == "edit"
        and control.get("visible") is True
        and control.get("enabled") is True
    ]
    inside = [(i, c) for i, c in usable if c.get("inside_picker") is True]
    known_names = {"szukaj", "wyszukaj", "search", "filter", "filtr", "find"}
    named = [(i, c) for i, c in usable
             if str(c.get("name") or "").casefold().strip() in known_names]

    # A true UIA descendant of IDC_ZAMAWIAJACY is stronger than an edit
    # which merely overlaps its rectangle. Prefer it only if unique.
    structural = [(i, c) for i, c in inside if c.get("structural_child") is True]
    if len(structural) == 1:
        return CustomerSearchDecision(
            "type_in_unique_search_edit", "unique_customer_picker_child",
            len(inside), structural[0][0],
        )
    # Inside-picker candidates are stronger than a similarly named field
    # elsewhere on the document. Restrict to this group first.
    candidates = structural if len(structural) > 1 else inside if inside else named
    if len(candidates) == 1:
        return CustomerSearchDecision("type_in_unique_search_edit",
                                      "verified_search_edit", 1, candidates[0][0])
    if len(candidates) > 1:
        focused = [(i, c) for i, c in candidates if c.get("focused") is True]
        if len(focused) == 1:
            return CustomerSearchDecision(
                "type_in_unique_search_edit", "focused_search_edit_inside_lookup"
                if inside else "focused_named_search_edit",
                len(candidates), focused[0][0]
            )
        return CustomerSearchDecision("blocked", "multiple_possible_search_edits",
                                      len(candidates))
    if picker_focused:
        return CustomerSearchDecision("typeahead_on_focused_lookup",
                                      "focused_verified_picker", 0)
    return CustomerSearchDecision("blocked", "no_edit_and_picker_not_focused", 0)


def type_customer_search(scene: Any, customer_name: str) -> CustomerSearchDecision:
    if not isinstance(customer_name, str) or not customer_name.strip() or len(customer_name) > 100:
        return CustomerSearchDecision("blocked", "invalid_customer_name")
    meta = scene.observation.metadata
    hwnd = meta.get("window_handle")
    if not isinstance(hwnd, int) or hwnd <= 0:
        return CustomerSearchDecision("blocked", "invalid_document_hwnd")

    from pywinauto import Desktop
    from app.agent.perception.windowhub_ui_automation_provider import WindowHubUIAutomationProvider

    matching = [e for e in scene.elements
                if (e.metadata or {}).get("automation_id") == "IDC_ZAMAWIAJACY"
                and (e.metadata or {}).get("uia_visible") is True
                and (e.metadata or {}).get("uia_enabled") is True]
    if len(matching) != 1:
        return CustomerSearchDecision("blocked", "picker_not_unique")
    rid = (matching[0].metadata or {}).get("uia_runtime_id")
    if not isinstance(rid, str) or not rid.strip():
        return CustomerSearchDecision("blocked", "picker_runtime_id_missing")

    import ctypes
    from ctypes import wintypes
    win = ctypes.WinDLL("user32", use_last_error=True)
    win.GetForegroundWindow.argtypes = []
    win.GetForegroundWindow.restype = wintypes.HWND
    if int(win.GetForegroundWindow() or 0) != hwnd:
        return CustomerSearchDecision("blocked", "document_not_foreground")

    root = Desktop(backend="uia").window(handle=hwnd).wrapper_object()
    wrappers = [root, *root.descendants()]
    native_picker = [
        w for w in wrappers
        if _native_matches(w, "IDC_ZAMAWIAJACY", rid,
                           WindowHubUIAutomationProvider)
    ]
    if len(native_picker) != 1:
        return CustomerSearchDecision("blocked", "native_picker_not_unique")

    picker = native_picker[0]
    all_edits = []
    picker_descendants = set()
    try:
        picker_descendants = {
            WindowHubUIAutomationProvider._runtime_id(w) for w in picker.descendants()
        }
    except Exception:
        pass

    for w in wrappers:
        try:
            info = w.element_info
            if str(info.control_type or "").casefold() != "edit":
                continue
            if not info.enabled or not info.visible:
                continue
            all_edits.append({
                "wrapper": w,
                "role": "edit",
                "visible": True,
                "enabled": True,
                "name": str(info.name or "").strip(),
                "inside_picker": WindowHubUIAutomationProvider._runtime_id(w) in picker_descendants,
                "structural_child": WindowHubUIAutomationProvider._runtime_id(w) in picker_descendants,
                "focused": bool(getattr(info, "has_keyboard_focus", False)),
            })
        except Exception:
            continue

    # A generic 'Search' field in the parent document must not be chosen
    # if it is elsewhere. Require physical containment in the lookup area.
    try:
        pr = picker.rectangle()
        for item in all_edits:
            rr = item["wrapper"].rectangle()
            inside = (
                rr.left >= pr.left and rr.right <= pr.right
                and rr.top >= pr.top and rr.bottom <= pr.bottom
            )
            item["inside_picker"] = item["inside_picker"] or inside
    except Exception:
        pass
    decision = classify_customer_search_controls(
        all_edits, picker_focused=bool((matching[0].metadata or {}).get("uia_focused"))
    )
    print("CUSTOMER_SEARCH_EDITS_TOTAL =", len(all_edits))
    print("CUSTOMER_SEARCH_EDITS_INSIDE_LOOKUP =", sum(
        item["inside_picker"] for item in all_edits
    ))
    print("CUSTOMER_SEARCH_EDITS_FOCUSED =", sum(
        item["focused"] for item in all_edits
    ))
    if decision.status == "blocked":
        return decision

    try:
        if decision.status == "type_in_unique_search_edit":
            if decision.selected_index is None:
                return CustomerSearchDecision("blocked", "search_edit_identity_missing")
            edit = all_edits[decision.selected_index]["wrapper"]
            edit.set_focus()
            try:
                edit.set_edit_text(customer_name)
            except Exception:
                # No blind fallback to another field.
                return CustomerSearchDecision("blocked", "edit_does_not_support_safe_set_value")
        else:
            # Only if UIA reports the picker focused; send once, never Enter.
            from pywinauto.keyboard import send_keys
            send_keys(customer_name, with_spaces=True, pause=0.06)
    except Exception as exc:
        return CustomerSearchDecision("blocked", "input_failed_" + type(exc).__name__)
    return CustomerSearchDecision("search_submitted_unverified",
                                  decision.status, decision.search_control_count)


def _native_matches(wrapper, automation_id, runtime_id, provider):
    try:
        return (
            str(wrapper.element_info.automation_id) == automation_id
            and provider._runtime_id(wrapper) == runtime_id
            and bool(wrapper.element_info.enabled)
            and bool(wrapper.element_info.visible)
        )
    except Exception:
        return False
