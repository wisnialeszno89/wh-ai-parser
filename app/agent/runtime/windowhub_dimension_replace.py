"""Replace WindowHub's populated dimension edit by native UIA identity.

Treat replacing an existing value (e.g. 1000 -> 1500) as one atomic
business operation, never append. This is Windows-only and fail-closed.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.agent.learning.windowhub_demonstration import stage_of
from app.agent.offers.windowhub_offer_form_map import WindowHubOfferFormMap
from app.agent.perception.windowhub_ui_automation_provider import WindowHubUIAutomationProvider


@dataclass(frozen=True)
class DimensionReplaceResult:
    status: str
    reason: str
    previous_value: str | None = None
    observed_value: str | None = None


def classify_replace(current: str | None, desired: int) -> str:
    if not isinstance(desired, int) or isinstance(desired, bool) or not 100 <= desired <= 5000:
        raise ValueError("dimension_out_of_range")
    if current is None:
        return "unknown"
    normalized = current.strip()
    if normalized == str(desired):
        return "already_satisfied"
    return "replace_existing" if normalized else "fill_empty"


def current_dimension(scene, field_name: str) -> str | None:
    if stage_of(scene) != "dimensions" or field_name not in {"width_1", "height_1"}:
        return None
    snapshot = WindowHubOfferFormMap().inspect(scene)
    match = snapshot.field(field_name) if snapshot else None
    if not match or not match.is_unique or match.element is None:
        return None
    return (match.element.metadata or {}).get("current_value")


def _resolve_native_field(scene, field_name: str, *, desktop=None):
    """Resolve one foreground native Edit against UIA ID, RuntimeId and bounds."""
    import ctypes
    from ctypes import wintypes
    from pywinauto import Desktop

    if stage_of(scene) != "dimensions":
        raise ValueError("not_dimensions_stage")
    snapshot = WindowHubOfferFormMap().inspect(scene)
    match = snapshot.field(field_name) if snapshot is not None else None
    if match is None or not match.is_unique or match.enabled is not True or match.element is None:
        raise ValueError("dimension_edit_missing_or_ambiguous")
    element = match.element
    metadata = element.metadata or {}
    if (element.kind != "edit" or metadata.get("source") not in {
        "windows_ui_automation", "windowhub_ui_automation",
    } or metadata.get("uia_enabled") is not True
        or metadata.get("uia_visible") is not True
        or not isinstance(metadata.get("uia_runtime_id"), str)
        or not metadata["uia_runtime_id"]):
        raise ValueError("dimension_edit_identity_invalid")
    hwnd = scene.observation.metadata.get("window_handle")
    rect = scene.observation.metadata.get("window_rect")
    if not isinstance(hwnd, int) or hwnd <= 0 or rect is None:
        raise ValueError("dimension_window_geometry_missing")
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetForegroundWindow.argtypes = []
    user32.GetForegroundWindow.restype = wintypes.HWND
    if int(user32.GetForegroundWindow() or 0) != hwnd:
        raise ValueError("windowhub_not_foreground")
    expected_rect = (
        int(rect.left) + element.x,
        int(rect.top) + element.y,
        int(rect.left) + element.x + element.width,
        int(rect.top) + element.y + element.height,
    )
    matches = []
    root = (desktop or Desktop(backend="uia")).window(handle=hwnd).wrapper_object()
    for wrapper in root.descendants():
        try:
            info = wrapper.element_info
            area = wrapper.rectangle()
            actual = (int(area.left), int(area.top), int(area.right), int(area.bottom))
            if (str(info.control_type).strip().casefold() == "edit"
                and str(info.automation_id) == metadata.get("automation_id")
                and WindowHubUIAutomationProvider._runtime_id(wrapper) == metadata["uia_runtime_id"]
                and bool(info.enabled) and bool(info.visible)
                and actual == expected_rect):
                matches.append(wrapper)
        except Exception:
            continue
    if len(matches) != 1:
        raise ValueError("fresh_dimension_field_not_unique")
    return matches[0]


def replace_dimension_once(loop, *, field_name: str, desired: int) -> DimensionReplaceResult:
    """One attempt; no control-loop automatic duplicate WRITE and no blind retry."""
    if field_name not in {"width_1", "height_1"}:
        raise ValueError("unsupported_dimension_field")
    classify_replace("", desired)
    scene = loop.observe_scene()
    existing = current_dimension(scene, field_name)
    mode = classify_replace(existing, desired)
    if mode == "already_satisfied":
        return DimensionReplaceResult("verified", "already_satisfied", existing, existing)
    if mode == "unknown":
        return DimensionReplaceResult("blocked", "current_value_not_observable", None)
    print(f"DIMENSION_FIELD={field_name} MODE={mode} EXISTING_VALUE={existing!r} TARGET={desired}")
    try:
        wrapper = _resolve_native_field(scene, field_name)
    except Exception as exc:
        return DimensionReplaceResult("blocked", "native_scope_" + type(exc).__name__, existing)

    # Prefer UIA ValuePattern, which replaces the whole value rather than
    # placing a cursor and inserting. No fallback to blind keyboard typing.
    try:
        pattern = wrapper.iface_value
        if pattern is None or bool(pattern.CurrentIsReadOnly):
            return DimensionReplaceResult("blocked", "native_value_pattern_not_writable", existing)
        before_native = pattern.CurrentValue
        if isinstance(before_native, str) and before_native.strip() != existing.strip():
            return DimensionReplaceResult("blocked", "native_value_changed_since_observation", existing, before_native)
        pattern.SetValue(str(desired))
    except Exception as exc:
        return DimensionReplaceResult("blocked", "native_set_value_" + type(exc).__name__, existing)

    # If Windows/DevExpress commit on focus-loss, first inspect, then make
    # a bounded focus move only if needed. Never call WRITE a second time.
    after = loop.observe_scene()
    actual = current_dimension(after, field_name)
    if isinstance(actual, str) and actual.strip() == str(desired):
        return DimensionReplaceResult("verified", "native_value_readback", existing, actual)
    return DimensionReplaceResult("blocked", "post_write_readback_mismatch", existing, actual)
