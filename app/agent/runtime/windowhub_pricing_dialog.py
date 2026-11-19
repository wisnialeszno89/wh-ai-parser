"""Resolve the current-position pricing sheet from live native controls."""
from __future__ import annotations

from decimal import Decimal
import re


PRICING_TITLE = "wycena bieżącej pozycji"
ACCEPT_NEW_PRICE = "przyjmij nową wycenę"
DISCOUNT_LABELS = {"rabat", "rabat [%]", "rabat (%)", "rabat %"}


def parse_discount(value):
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r"\s*(\d{1,3}(?:[,.]\d{1,2})?)\s*%?\s*", value)
    if not match:
        return None
    discount = Decimal(match[1].replace(",", "."))
    return discount if discount <= 100 else None


def label(name):
    return " ".join(name.casefold().replace("&", "").strip(" :-–").split())


def discount_control(edits, captions, name):
    """Prefer the associated edit label, else prove a unique same-row peer."""
    named = [edit for edit in edits if label(name(edit)) in DISCOUNT_LABELS]
    if named:
        return named[0] if len(named) == 1 else None
    labels = [caption.rectangle() for caption in captions if label(name(caption)) in DISCOUNT_LABELS]
    if len(labels) != 1:
        return None
    caption = labels[0]
    center = (caption.top + caption.bottom) / 2
    peers = []
    for edit in edits:
        rect = edit.rectangle()
        # Require alignment and adjacency to this label, not a particular
        # screen coordinate or a value (VAT and markup are also percentages).
        if rect.top <= center < rect.bottom and 0 <= rect.left - caption.right <= (rect.bottom - rect.top) * 3:
            peers.append(edit)
    return peers[0] if len(peers) == 1 else None


def native_pricing_controls(hwnd):
    from pywinauto import Desktop

    for backend in ("uia", "win32"):
        try:
            dialog = Desktop(backend=backend).window(handle=hwnd).wrapper_object()
            if backend == "uia":
                def name(w):
                    return w.element_info.name or ""

                edits = dialog.descendants(control_type="Edit")
                captions = dialog.descendants(control_type="Text")
                buttons = dialog.descendants(control_type="Button")
            else:
                def name(w):
                    return w.window_text()

                edits = dialog.descendants(class_name="Edit")
                captions = dialog.descendants(class_name="Static")
                buttons = dialog.descendants(class_name="Button")

            field = discount_control([w for w in edits if w.is_visible()], [w for w in captions if w.is_visible()], name)
            accept = [w for w in buttons if w.is_visible() and w.is_enabled() and label(name(w)) == ACCEPT_NEW_PRICE]
            if field is None or len(accept) != 1:
                continue
            if backend == "uia":
                value = field.iface_value
                invoke = accept[0].iface_invoke.Invoke
                return lambda: value.CurrentValue, value.SetValue if not value.CurrentIsReadOnly else None, invoke
            return field.window_text, field.set_edit_text if field.is_enabled() else None, accept[0].click
        except Exception as exc:
            print("WH_PRICING_NATIVE_" + backend.upper() + "=" + type(exc).__name__, flush=True)
    return None


def confirm_position_pricing(hwnd, discount, *, still_owned):
    """Accept exactly one calculation after fresh readback of the discount."""
    if not still_owned():
        return False
    controls = native_pricing_controls(hwnd)
    if controls is None or not still_owned():
        print("WH_PRICING_EVIDENCE=discount_or_accept_control_unverified", flush=True)
        return False

    read, write, _ = controls
    raw = read()
    current = parse_discount(raw)
    if current is None:
        print("WH_PRICING_EVIDENCE=current_discount_unreadable", flush=True)
        return False
    if current != discount:
        if write is None or not still_owned():
            return False
        formatted = format(discount, "f").replace(".", "," if "," in raw else ".")
        write(formatted)

    if not still_owned():
        return False
    fresh = native_pricing_controls(hwnd)
    if fresh is None or parse_discount(fresh[0]()) != discount or not still_owned():
        print("WH_PRICING_EVIDENCE=requested_discount_readback_unverified", flush=True)
        return False
    print(f"WH_PRICING_DISCOUNT_VERIFIED={discount}", flush=True)
    fresh[2]()
    return True
