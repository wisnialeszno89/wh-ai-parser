"""Read-only diagnostic for WindowHub form-field document scope.

Prints semantic labels and UI Automation structure only. It never prints
control values, invokes the planner, or executes a GUI action.
"""
from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _robot_execution_mode(control_loop):
    from app.agent.execution.robot_gui_executor import RobotGUIExecutor

    executors = control_loop.verification_loop.execution_engine.registry.all()
    matches = [item for item in executors if isinstance(item, RobotGUIExecutor)]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one RobotGUIExecutor; found {len(matches)}."
        )
    return matches[0].robot_action_executor.mode


def _positive_handle(value):
    try:
        handle = int(value)
    except (TypeError, ValueError, OSError):
        return None
    return handle if handle > 0 else None


def _native_window_relationships(native_handle, root_handle):
    """Compare a control's real HWND ancestry with the observed WindowHub HWND.

    The UIA enumeration handle only describes which wrapper was walked. It
    does not prove that every returned control is a native descendant of that
    window, so this helper separately asks Win32 for root/owner relationships.
    """
    native = _positive_handle(native_handle)
    root = _positive_handle(root_handle)
    result = {
        "uia_native_handle_present": native is not None,
        "native_window_relation_available": False,
        "native_root_matches_observed_window": None,
        "native_root_owner_matches_observed_window": None,
        "native_parent_matches_observed_window": None,
        "native_owner_matches_observed_window": None,
        "in_observed_root_window": None,
        "native_owned_by_observed_window": None,
        "belongs_to_observed_window_or_owned_popup": None,
    }
    if os.name != "nt" or native is None or root is None:
        return result

    try:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        get_ancestor = user32.GetAncestor
        get_ancestor.argtypes = (ctypes.c_void_p, ctypes.c_uint)
        get_ancestor.restype = ctypes.c_void_p
        get_parent = user32.GetParent
        get_parent.argtypes = (ctypes.c_void_p,)
        get_parent.restype = ctypes.c_void_p
        get_window = user32.GetWindow
        get_window.argtypes = (ctypes.c_void_p, ctypes.c_uint)
        get_window.restype = ctypes.c_void_p

        hwnd = ctypes.c_void_p(native)
        native_root = int(get_ancestor(hwnd, 2) or 0)  # GA_ROOT
        native_root_owner = int(get_ancestor(hwnd, 3) or 0)  # GA_ROOTOWNER
        native_parent = int(get_parent(hwnd) or 0)
        native_owner = int(get_window(hwnd, 4) or 0)  # GW_OWNER
    except Exception:
        return result

    root_matches = native_root == root
    owner_root_matches = native_root_owner == root
    result.update({
        "native_window_relation_available": True,
        "native_root_matches_observed_window": root_matches,
        "native_root_owner_matches_observed_window": owner_root_matches,
        "native_parent_matches_observed_window": native_parent == root,
        "native_owner_matches_observed_window": native_owner == root,
        "in_observed_root_window": root_matches,
        "native_owned_by_observed_window": owner_root_matches,
        "belongs_to_observed_window_or_owned_popup": (
            root_matches or owner_root_matches
        ),
    })
    return result


def _normalized_window_text(value):
    if not isinstance(value, str):
        return ""
    return " ".join(value.split()).casefold()


def _native_client_bounds_screen(handle):
    """Return a Win32 client rectangle in screen coordinates, internally only."""
    hwnd_value = _positive_handle(handle)
    if os.name != "nt" or hwnd_value is None:
        return None
    try:
        user32 = ctypes.WinDLL("user32", use_last_error=True)

        class _RECT(ctypes.Structure):
            _fields_ = (
                ("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long),
            )

        class _POINT(ctypes.Structure):
            _fields_ = (("x", ctypes.c_long), ("y", ctypes.c_long))

        get_client_rect = user32.GetClientRect
        get_client_rect.argtypes = (ctypes.c_void_p, ctypes.POINTER(_RECT))
        get_client_rect.restype = ctypes.c_int
        client_to_screen = user32.ClientToScreen
        client_to_screen.argtypes = (ctypes.c_void_p, ctypes.POINTER(_POINT))
        client_to_screen.restype = ctypes.c_int

        hwnd = ctypes.c_void_p(hwnd_value)
        rect = _RECT()
        if not get_client_rect(hwnd, ctypes.byref(rect)):
            return None
        top_left = _POINT(rect.left, rect.top)
        bottom_right = _POINT(rect.right, rect.bottom)
        if not (
            client_to_screen(hwnd, ctypes.byref(top_left))
            and client_to_screen(hwnd, ctypes.byref(bottom_right))
            and bottom_right.x > top_left.x
            and bottom_right.y > top_left.y
        ):
            return None
        return (
            int(top_left.x), int(top_left.y),
            int(bottom_right.x), int(bottom_right.y),
        )
    except Exception:
        return None


def _native_child_window_snapshot(root_handle):
    """Enumerate native child HWNDs without returning their names to callers."""
    root = _positive_handle(root_handle)
    if os.name != "nt" or root is None:
        return None

    try:
        user32 = ctypes.WinDLL("user32", use_last_error=True)

        enum_proc_type = ctypes.WINFUNCTYPE(
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_ssize_t,
        )
        get_text = user32.GetWindowTextW
        get_text.argtypes = (ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int)
        get_text.restype = ctypes.c_int
        get_text_length = user32.GetWindowTextLengthW
        get_text_length.argtypes = (ctypes.c_void_p,)
        get_text_length.restype = ctypes.c_int
        get_class = user32.GetClassNameW
        get_class.argtypes = (ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int)
        get_class.restype = ctypes.c_int
        is_visible = user32.IsWindowVisible
        is_visible.argtypes = (ctypes.c_void_p,)
        is_visible.restype = ctypes.c_int

        class _RECT(ctypes.Structure):
            _fields_ = (
                ("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long),
            )

        class _POINT(ctypes.Structure):
            _fields_ = (
                ("x", ctypes.c_long),
                ("y", ctypes.c_long),
            )

        get_client_rect = user32.GetClientRect
        get_client_rect.argtypes = (ctypes.c_void_p, ctypes.POINTER(_RECT))
        get_client_rect.restype = ctypes.c_int
        client_to_screen = user32.ClientToScreen
        client_to_screen.argtypes = (ctypes.c_void_p, ctypes.POINTER(_POINT))
        client_to_screen.restype = ctypes.c_int
        enum_children = user32.EnumChildWindows
        enum_children.argtypes = (ctypes.c_void_p, enum_proc_type, ctypes.c_ssize_t)
        enum_children.restype = ctypes.c_int

        windows = []

        def add_window(raw_handle, _lparam):
            handle = _positive_handle(raw_handle)
            if handle is None:
                return True
            hwnd = ctypes.c_void_p(handle)

            text_length = max(0, int(get_text_length(hwnd)))
            title_buffer = ctypes.create_unicode_buffer(min(text_length + 1, 2048))
            if title_buffer:
                get_text(hwnd, title_buffer, len(title_buffer))

            class_buffer = ctypes.create_unicode_buffer(256)
            get_class(hwnd, class_buffer, len(class_buffer))

            client_bounds_screen = None
            client_rect = _RECT()
            try:
                if get_client_rect(hwnd, ctypes.byref(client_rect)):
                    top_left = _POINT(client_rect.left, client_rect.top)
                    bottom_right = _POINT(client_rect.right, client_rect.bottom)
                    if (
                        client_to_screen(hwnd, ctypes.byref(top_left))
                        and client_to_screen(hwnd, ctypes.byref(bottom_right))
                        and bottom_right.x > top_left.x
                        and bottom_right.y > top_left.y
                    ):
                        client_bounds_screen = (
                            int(top_left.x),
                            int(top_left.y),
                            int(bottom_right.x),
                            int(bottom_right.y),
                        )
            except Exception:
                client_bounds_screen = None

            windows.append({
                "handle": handle,
                "title": title_buffer.value,
                "class_name": class_buffer.value,
                "visible": bool(is_visible(hwnd)),
                # Kept in memory for a boolean relation check only; the
                # rectangle and HWND are never serialized into the report.
                "client_bounds_screen": client_bounds_screen,
            })
            return True

        callback = enum_proc_type(add_window)
        succeeded = bool(enum_children(ctypes.c_void_p(root), callback, 0))
        if not succeeded:
            return None
        return tuple(windows)
    except Exception:
        return None


def _native_document_window_geometry_summary(exact_windows):
    """Report counts for visible active-document client rectangles only."""
    records = tuple(exact_windows or ())
    return {
        "exact_title_match_count": len(records),
        "visible_exact_title_match_count": sum(
            item.get("visible") is True for item in records
        ),
        "client_bounds_available_exact_title_match_count": sum(
            isinstance(item.get("client_bounds_screen"), (tuple, list))
            and len(item.get("client_bounds_screen")) == 4
            for item in records
        ),
    }


def _field_document_window_geometry(
    field,
    *,
    exact_active_document_windows=(),
    root_window_rect=None,
):
    """Compare field bounds to the unique document window without exposing geometry."""
    unknown = {
        "active_document_client_geometry_available": False,
        "field_bounds_fully_within_active_document_client_area": None,
        "field_bounds_intersect_active_document_client_area": None,
    }
    windows = tuple(exact_active_document_windows or ())
    if len(windows) != 1:
        return unknown

    window = windows[0]
    if window.get("visible") is not True:
        return unknown
    screen_bounds = window.get("client_bounds_screen")
    if not isinstance(screen_bounds, (tuple, list)) or len(screen_bounds) != 4:
        return unknown

    def rect_value(rect, key):
        if isinstance(rect, dict):
            return rect.get(key)
        return getattr(rect, key, None)

    try:
        root_left = int(rect_value(root_window_rect, "left"))
        root_top = int(rect_value(root_window_rect, "top"))
        field_element = getattr(field, "element", None)
        field_left = int(getattr(field_element, "x"))
        field_top = int(getattr(field_element, "y"))
        field_width = int(getattr(field_element, "width"))
        field_height = int(getattr(field_element, "height"))
        doc_left = int(screen_bounds[0]) - root_left
        doc_top = int(screen_bounds[1]) - root_top
        doc_right = int(screen_bounds[2]) - root_left
        doc_bottom = int(screen_bounds[3]) - root_top
    except (TypeError, ValueError, AttributeError, OverflowError):
        return unknown

    if (
        field_width <= 0
        or field_height <= 0
        or doc_right <= doc_left
        or doc_bottom <= doc_top
    ):
        return unknown

    field_right = field_left + field_width
    field_bottom = field_top + field_height
    intersects = (
        field_left < doc_right
        and field_right > doc_left
        and field_top < doc_bottom
        and field_bottom > doc_top
    )
    fully_contained = (
        field_left >= doc_left
        and field_top >= doc_top
        and field_right <= doc_right
        and field_bottom <= doc_bottom
    )
    return {
        "active_document_client_geometry_available": True,
        "field_bounds_fully_within_active_document_client_area": fully_contained,
        "field_bounds_intersect_active_document_client_area": intersects,
    }



def _field_coordinate_origin_probe(
    field,
    *,
    exact_active_document_windows=(),
    root_window_rect=None,
    root_client_bounds_screen=None,
):
    """Compare UIA field bounds in several candidate origins, returning counts only.

    UIA rectangles and Win32 client rectangles may be expressed relative to
    different coordinate origins. This probe keeps every coordinate in memory
    and reports only whether a candidate origin yields an overlap. It is
    diagnostic evidence only and must never establish document scope.
    """
    unknown = {
        "available": False,
        "root_relative_intersects": None,
        "screen_relative_intersects": None,
        "root_client_relative_intersects": None,
    }
    windows = tuple(exact_active_document_windows or ())
    if len(windows) != 1 or windows[0].get("visible") is not True:
        return unknown
    bounds = windows[0].get("client_bounds_screen")
    if not isinstance(bounds, (tuple, list)) or len(bounds) != 4:
        return unknown

    def rect_value(rect, key):
        if isinstance(rect, dict):
            return rect.get(key)
        return getattr(rect, key, None)

    try:
        element = getattr(field, "element", None)
        field_left = int(getattr(element, "x"))
        field_top = int(getattr(element, "y"))
        field_width = int(getattr(element, "width"))
        field_height = int(getattr(element, "height"))
        screen_left, screen_top, screen_right, screen_bottom = (
            int(value) for value in bounds
        )
        root_left = int(rect_value(root_window_rect, "left"))
        root_top = int(rect_value(root_window_rect, "top"))
        root_right = int(rect_value(root_window_rect, "right"))
        root_bottom = int(rect_value(root_window_rect, "bottom"))
        if not (
            isinstance(root_client_bounds_screen, (tuple, list))
            and len(root_client_bounds_screen) == 4
        ):
            return unknown
        client_left, client_top, client_right, client_bottom = (
            int(value) for value in root_client_bounds_screen
        )
    except (TypeError, ValueError, AttributeError, OverflowError):
        return unknown

    if (
        field_width <= 0 or field_height <= 0
        or screen_right <= screen_left or screen_bottom <= screen_top
        or root_right <= root_left or root_bottom <= root_top
        or client_right <= client_left or client_bottom <= client_top
    ):
        return unknown

    def intersects(left, top, right, bottom):
        return (
            field_left < right and field_left + field_width > left
            and field_top < bottom and field_top + field_height > top
        )

    # Candidate A: convert the native client rectangle to coordinates whose
    # origin is the top-left of the observed root window.
    root_relative = (
        screen_left - root_left,
        screen_top - root_top,
        screen_right - root_left,
        screen_bottom - root_top,
    )
    # Candidate B: UIA field bounds are already screen-relative.
    screen_relative = (screen_left, screen_top, screen_right, screen_bottom)
    # Candidate C: use the actual root HWND client origin from Win32,
    # converted to screen coordinates with ClientToScreen.
    root_client_relative = (
        screen_left - client_left,
        screen_top - client_top,
        screen_right - client_left,
        screen_bottom - client_top,
    )
    return {
        "available": True,
        "root_relative_intersects": intersects(*root_relative),
        "screen_relative_intersects": intersects(*screen_relative),
        "root_client_relative_intersects": intersects(*root_client_relative),
    }


def _native_window_title_matches(active_document, windows):
    """Return internal candidate records plus a sanitized count summary."""
    normalized_document = _normalized_window_text(active_document)
    if windows is None or not normalized_document:
        return (), {
            "available": windows is not None,
            "descendant_native_window_count": len(windows) if windows is not None else None,
            "active_document_exact_title_match_count": None,
            "active_document_substring_title_match_count": None,
        }

    exact = tuple(
        item for item in windows
        if _normalized_window_text(item.get("title")) == normalized_document
    )
    substring = tuple(
        item for item in windows
        if (
            normalized_document in _normalized_window_text(item.get("title"))
            or _normalized_window_text(item.get("title")) in normalized_document
        )
        and _normalized_window_text(item.get("title"))
    )
    return exact, {
        "available": True,
        "descendant_native_window_count": len(windows),
        "active_document_exact_title_match_count": len(exact),
        "active_document_substring_title_match_count": len(substring),
    }


def _native_parent_chain(handle):
    """Return an internal HWND parent chain, or None when Win32 lookup fails."""
    start = _positive_handle(handle)
    if os.name != "nt" or start is None:
        return None
    try:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        get_parent = user32.GetParent
        get_parent.argtypes = (ctypes.c_void_p,)
        get_parent.restype = ctypes.c_void_p

        chain = [start]
        current = start
        for _ in range(64):
            parent = _positive_handle(get_parent(ctypes.c_void_p(current)))
            if parent is None or parent == current:
                break
            chain.append(parent)
            current = parent
        return tuple(chain)
    except Exception:
        return None


def _field_diagnostic(
    field,
    *,
    root_handle=None,
    native_relationships=None,
    active_document=None,
    selected_document_tab_native_handle=None,
    exact_active_document_window_handles=(),
    native_child_window_probe_available=False,
    exact_active_document_windows=(),
    observed_root_window_rect=None,
):
    """Return field scope facts while deliberately excluding all field values."""
    metadata = getattr(field.element, "metadata", None) or {}
    ancestry = []

    for item in metadata.get("uia_ancestor_context", ()) or ():
        if not isinstance(item, (tuple, list)) or len(item) < 2:
            continue
        control_type, class_name = item[0], item[1]
        control_type = str(control_type or "?").strip() or "?"
        class_name = str(class_name or "?").strip() or "?"
        # Exclude ancestor names: they can contain document-specific text.
        ancestry.append(f"{control_type}<{class_name}>")

    current_value = getattr(field, "value", None)
    observed_handle = metadata.get("uia_window_handle")
    native_relationships = (
        native_relationships
        if native_relationships is not None
        else _native_window_relationships(
            metadata.get("uia_native_handle"),
            root_handle,
        )
    )

    # Compare names privately; never print ancestor names, since UIA can
    # expose customer/document text in parent window names.
    normalized_document = (
        active_document.strip().casefold()
        if isinstance(active_document, str) and active_document.strip()
        else None
    )
    ancestor_context = metadata.get("uia_ancestor_context", ()) or ()
    ancestor_name_exact_match = False
    window_ancestor_name_exact_match = False
    named_window_ancestor_count = 0
    for item in ancestor_context:
        if not isinstance(item, (tuple, list)) or len(item) < 3:
            continue
        control_type = str(item[0] or "").strip().casefold()
        name = item[2]
        if not isinstance(name, str) or not name.strip():
            continue
        if control_type == "window":
            named_window_ancestor_count += 1
        if normalized_document is not None and name.strip().casefold() == normalized_document:
            ancestor_name_exact_match = True
            if control_type == "window":
                window_ancestor_name_exact_match = True

    field_native_handle = _positive_handle(metadata.get("uia_native_handle"))
    selected_tab_handle = _positive_handle(selected_document_tab_native_handle)
    ancestor_native_handles = [
        handle
        for item in ancestor_context
        if isinstance(item, (tuple, list)) and len(item) >= 4
        and (handle := _positive_handle(item[3])) is not None
    ]

    field_or_ancestor_native_handle_match = None
    native_parent_chain_matches_active_document_window = None
    if native_child_window_probe_available:
        exact_handles = tuple(
            handle
            for raw in exact_active_document_window_handles
            if (handle := _positive_handle(raw)) is not None
        )
        if not exact_handles:
            field_or_ancestor_native_handle_match = False
            native_parent_chain_matches_active_document_window = False
        else:
            observed_handles = []
            if field_native_handle is not None:
                observed_handles.append(field_native_handle)
            observed_handles.extend(ancestor_native_handles)
            field_or_ancestor_native_handle_match = any(
                handle in exact_handles for handle in observed_handles
            )

            chains = [
                _native_parent_chain(handle)
                for handle in observed_handles
            ]
            known_chains = [chain for chain in chains if chain is not None]
            if any(set(chain).intersection(exact_handles) for chain in known_chains):
                native_parent_chain_matches_active_document_window = True
            elif observed_handles and len(known_chains) == len(observed_handles):
                native_parent_chain_matches_active_document_window = False

    geometry_diagnostic = _field_document_window_geometry(
        field,
        exact_active_document_windows=exact_active_document_windows,
        root_window_rect=observed_root_window_rect,
    )

    return {
        "label": field.label,
        "control_type": field.control_type,
        "document_scope": field.document_scope,
        "scope_status": field.scope_status,
        "uia_tab_scope": metadata.get("uia_tab_scope"),
        "uia_document_tab_selected": metadata.get(
            "uia_document_tab_selected"
        ),
        # This records which wrapper was enumerated; actual HWND ancestry is
        # reported separately and determines in_observed_root_window.
        "enumerated_by_observed_window": (
            root_handle is not None and observed_handle == root_handle
        ),
        **native_relationships,
        **geometry_diagnostic,
        "owned_modal": metadata.get("uia_owned_modal") is True,
        "active_document_ancestor_name_exact_match": ancestor_name_exact_match,
        "active_document_window_ancestor_name_exact_match": (
            window_ancestor_name_exact_match
        ),
        "named_window_ancestor_count": named_window_ancestor_count,
        # Correlation only: equal HWNDs are diagnostic clues, not sufficient
        # to infer document ownership or authorize reading/writing a field.
        "selected_document_tab_native_handle_present": selected_tab_handle is not None,
        "field_native_handle_present": field_native_handle is not None,
        "field_native_handle_matches_selected_document_tab": (
            field_native_handle == selected_tab_handle
            if field_native_handle is not None and selected_tab_handle is not None
            else None
        ),
        "ancestor_native_handle_available_count": len(ancestor_native_handles),
        "ancestor_native_handle_matches_selected_document_tab": (
            selected_tab_handle in ancestor_native_handles
            if selected_tab_handle is not None and ancestor_native_handles
            else (False if selected_tab_handle is not None else None)
        ),
        "field_or_ancestor_handle_matches_active_document_title_window": (
            field_or_ancestor_native_handle_match
        ),
        "native_parent_chain_matches_active_document_title_window": (
            native_parent_chain_matches_active_document_window
        ),
        "current_value_present": (
            isinstance(current_value, str) and bool(current_value.strip())
        ),
        "ancestor_structure": ancestry,
    }



_UIA_DIAGNOSTIC_CONTROL_TYPES = (
    "edit",
    "combobox",
    "button",
    "tabitem",
    "text",
    "pane",
    "window",
    "custom",
    "document",
    "group",
    "other",
)
_UIA_FORM_FIELD_TYPES = frozenset({"edit", "combobox"})
_UIA_NONSTANDARD_CANDIDATE_TYPES = (
    "custom",
    "other",
    "document",
    "group",
    "pane",
    "window",
    "button",
    "text",
)
_UIA_PATTERN_NAMES = (
    "value",
    "legacy_iaccessible",
    "text",
    "range_value",
    "selection_item",
    "invoke",
    "expand_collapse",
)
_UIA_CLASS_BUCKETS = (
    "windows_forms",
    "afx_mfc",
    "win32_edit",
    "win32_combobox",
    "win32_button",
    "win32_static_text",
    "class_unavailable",
    "other_class",
)


def _uia_class_bucket(class_name):
    """Reduce a native class name to a coarse, non-identifying category."""
    if not isinstance(class_name, str) or not class_name.strip():
        return "class_unavailable"
    normalized = class_name.strip().casefold()
    if "windowsforms" in normalized:
        return "windows_forms"
    if "afx:" in normalized or "afx" in normalized:
        return "afx_mfc"
    if "combobox" in normalized or "combo" in normalized:
        return "win32_combobox"
    if "edit" in normalized:
        return "win32_edit"
    if "button" in normalized:
        return "win32_button"
    if "static" in normalized or "text" in normalized:
        return "win32_static_text"
    return "other_class"


def _uia_pattern_available(item, pattern_name):
    """Check UIA pattern availability without invoking or reading a value."""
    try:
        return getattr(item, f"iface_{pattern_name}", None) is not None
    except Exception:
        return False


def _uia_nonstandard_candidate_summary(descendants, provider):
    """Summarize nonstandard UIA nodes and supported patterns using counts only."""
    counts = {
        control_type: {
            "count": 0,
            "visible_count": 0,
            "name_present_count": 0,
            "automation_id_present_count": 0,
            "positive_bounds_count": 0,
            "native_handle_present_count": 0,
            "window_text_method_present_count": 0,
            **{f"{name}_pattern_count": 0 for name in _UIA_PATTERN_NAMES},
            "value_pattern_current_value_read_count": 0,
            "value_pattern_current_value_nonempty_string_count": 0,
            "value_pattern_current_value_empty_string_count": 0,
            "value_pattern_current_value_nonstring_count": 0,
            "value_pattern_current_value_read_error_count": 0,
            "legacy_current_value_read_count": 0,
            "legacy_current_value_nonempty_string_count": 0,
            "legacy_current_value_empty_string_count": 0,
            "legacy_current_value_nonstring_count": 0,
            "legacy_current_value_read_error_count": 0,
        }
        for control_type in _UIA_NONSTANDARD_CANDIDATE_TYPES
    }
    class_buckets = {
        control_type: {bucket: 0 for bucket in _UIA_CLASS_BUCKETS}
        for control_type in ("custom", "other", "document", "group", "pane")
    }

    for item in descendants:
        try:
            info = item.element_info
            control_type = provider._normalize_control_type(
                getattr(info, "control_type", None)
            )
        except Exception:
            continue
        if control_type not in counts:
            continue

        row = counts[control_type]
        row["count"] += 1
        try:
            visible = bool(getattr(info, "visible", True))
            name = provider._string(getattr(info, "name", None))
            automation_id = provider._string(
                getattr(info, "automation_id", None)
            )
            class_name = getattr(info, "class_name", None)
            rectangle = item.rectangle()
            positive_bounds = (
                int(rectangle.width()) > 0 and int(rectangle.height()) > 0
            )
        except Exception:
            visible = False
            name = None
            automation_id = None
            class_name = None
            positive_bounds = False

        if visible:
            row["visible_count"] += 1
        if name:
            row["name_present_count"] += 1
        if automation_id:
            row["automation_id_present_count"] += 1
        if positive_bounds:
            row["positive_bounds_count"] += 1
        if provider._native_handle(item) is not None:
            row["native_handle_present_count"] += 1
        if callable(getattr(item, "window_text", None)):
            row["window_text_method_present_count"] += 1
        for pattern_name in _UIA_PATTERN_NAMES:
            if _uia_pattern_available(item, pattern_name):
                row[f"{pattern_name}_pattern_count"] += 1

        # Read ValuePattern/LegacyIAccessible values only to count whether a
        # value is retrievable. Never include the value itself in diagnostics.
        for pattern_name, prefix in (
            ("value", "value_pattern_current_value"),
            ("legacy_iaccessible", "legacy_current_value"),
        ):
            # A missing/unavailable pattern is not a failed value read.
            # Count a read error only after the pattern interface exists and
            # CurrentValue itself could not be retrieved.
            try:
                pattern_iface = getattr(item, f"iface_{pattern_name}", None)
            except Exception:
                continue
            if pattern_iface is None:
                continue
            try:
                current_value = getattr(pattern_iface, "CurrentValue")
            except Exception:
                row[f"{prefix}_read_error_count"] += 1
                continue
            row[f"{prefix}_read_count"] += 1
            if isinstance(current_value, str):
                if current_value.strip():
                    row[f"{prefix}_nonempty_string_count"] += 1
                else:
                    row[f"{prefix}_empty_string_count"] += 1
            else:
                row[f"{prefix}_nonstring_count"] += 1
            del current_value

        if control_type in class_buckets:
            bucket = _uia_class_bucket(class_name)
            class_buckets[control_type][bucket] += 1

    return {
        "by_control_type": counts,
        "class_bucket_counts": class_buckets,
    }


def _summarize_uia_field_candidates(
    descendants,
    *,
    provider,
    origin_x=0,
    origin_y=0,
    label_candidates=(),
    label_candidates_available=True,
):
    """Summarize UIA field-like descendants without returning private text."""
    type_counts = {name: 0 for name in _UIA_DIAGNOSTIC_CONTROL_TYPES}
    field_control_count = 0
    visible_field_control_count = 0
    visible_with_positive_bounds_count = 0
    visible_with_direct_name_count = 0
    visible_with_semantic_label_count = 0
    visible_with_positive_bounds_and_label_count = 0
    field_control_native_handle_present_count = 0
    field_control_metadata_read_failure_count = 0

    for item in descendants:
        try:
            element_info = item.element_info
            control_type = provider._normalize_control_type(
                getattr(element_info, "control_type", None)
            )
        except Exception:
            type_counts["other"] += 1
            continue

        bucket = (
            control_type
            if control_type in type_counts and control_type != "other"
            else "other"
        )
        type_counts[bucket] += 1

        if control_type not in _UIA_FORM_FIELD_TYPES:
            continue

        field_control_count += 1
        try:
            visible = bool(getattr(element_info, "visible", True))
            name = provider._string(getattr(element_info, "name", None))
            rectangle = item.rectangle()
            width = int(rectangle.width())
            height = int(rectangle.height())
            positive_bounds = width > 0 and height > 0
        except Exception:
            field_control_metadata_read_failure_count += 1
            continue

        if provider._native_handle(item) is not None:
            field_control_native_handle_present_count += 1

        if not visible:
            continue

        visible_field_control_count += 1
        if name:
            visible_with_direct_name_count += 1
        if positive_bounds:
            visible_with_positive_bounds_count += 1

        semantic_label = None
        try:
            semantic_label, _ = provider._resolve_semantic_label(
                item=item,
                name=name,
                control_type=control_type,
                rectangle=rectangle,
                origin_x=origin_x,
                origin_y=origin_y,
                label_candidates=label_candidates,
            )
        except Exception:
            semantic_label = None

        if semantic_label:
            visible_with_semantic_label_count += 1
        if positive_bounds and semantic_label:
            visible_with_positive_bounds_and_label_count += 1

    return {
        "available": True,
        "descendant_count": len(descendants),
        "control_type_counts": type_counts,
        "field_control_count": field_control_count,
        "field_control_visible_count": visible_field_control_count,
        "field_control_visible_with_positive_bounds_count": (
            visible_with_positive_bounds_count
        ),
        "field_control_visible_with_direct_name_count": (
            visible_with_direct_name_count
        ),
        "field_control_visible_with_semantic_label_count": (
            visible_with_semantic_label_count
        ),
        "field_control_visible_with_positive_bounds_and_semantic_label_count": (
            visible_with_positive_bounds_and_label_count
        ),
        "field_control_native_handle_present_count": (
            field_control_native_handle_present_count
        ),
        "field_control_metadata_read_failure_count": (
            field_control_metadata_read_failure_count
        ),
        "label_candidates_available": bool(label_candidates_available),
    }


def _uia_raw_field_candidate_census(root_handle, expected_title, window_rect=None):
    """Enumerate raw UIA controls and return counts only, never names or values."""
    root = _positive_handle(root_handle)
    if os.name != "nt" or root is None:
        return {
            "available": False,
            "failure_stage": "invalid_root_or_platform",
        }

    try:
        from app.agent.platform.windows_com import ensure_windows_sta
        ensure_windows_sta()

        from pywinauto import Desktop
        desktop = Desktop(backend="uia")
        window_spec = desktop.window(handle=root)
        wrapper = getattr(window_spec, "wrapper_object", None)
        window = wrapper() if callable(wrapper) else window_spec
        actual_title = window.window_text()
        if (
            isinstance(expected_title, str)
            and expected_title.strip()
            and actual_title.strip() != expected_title.strip()
        ):
            return {
                "available": False,
                "failure_stage": "window_title_mismatch",
            }
        descendants = tuple(window.descendants())
    except Exception:
        return {
            "available": False,
            "failure_stage": "uia_enumeration_failed",
        }

    origin_x = int(getattr(window_rect, "left", 0) or 0)
    origin_y = int(getattr(window_rect, "top", 0) or 0)
    from app.agent.perception.windowhub_ui_automation_provider import (
        WindowHubUIAutomationProvider,
    )
    provider = WindowHubUIAutomationProvider()

    try:
        label_candidates = provider._collect_label_candidates(
            descendants,
            origin_x=origin_x,
            origin_y=origin_y,
        )
        label_candidates_available = True
    except Exception:
        label_candidates = ()
        label_candidates_available = False

    summary = _summarize_uia_field_candidates(
        descendants,
        provider=provider,
        origin_x=origin_x,
        origin_y=origin_y,
        label_candidates=label_candidates,
        label_candidates_available=label_candidates_available,
    )
    summary["nonstandard_candidate_summary"] = (
        _uia_nonstandard_candidate_summary(descendants, provider)
    )
    summary["failure_stage"] = None
    return summary


def _scene_field_element_census(elements):
    """Compare provider-produced scene controls with the raw census."""
    counts = {
        "edit_count": 0,
        "combobox_count": 0,
        "ui_automation_edit_count": 0,
        "ui_automation_combobox_count": 0,
    }
    for element in elements:
        kind = str(getattr(element, "kind", "") or "").casefold()
        if kind not in _UIA_FORM_FIELD_TYPES:
            continue
        key = "edit_count" if kind == "edit" else "combobox_count"
        counts[key] += 1
        metadata = getattr(element, "metadata", None) or {}
        if metadata.get("source") == "windowhub_ui_automation":
            uia_key = (
                "ui_automation_edit_count"
                if kind == "edit"
                else "ui_automation_combobox_count"
            )
            counts[uia_key] += 1
    counts["scene_field_control_count"] = (
        counts["edit_count"] + counts["combobox_count"]
    )
    counts["ui_automation_field_control_count"] = (
        counts["ui_automation_edit_count"]
        + counts["ui_automation_combobox_count"]
    )
    return counts


def main() -> int:
    if os.name != "nt":
        print("FAIL: WindowHub field-scope diagnostic requires Windows.", file=sys.stderr)
        return 2

    if os.environ.get("WH_REAL_WINDOWHUB", "").strip() == "1":
        print(
            "FAIL: WH_REAL_WINDOWHUB=1 selects LIVE execution. "
            "Unset it before running this read-only diagnostic.",
            file=sys.stderr,
        )
        return 2

    try:
        from app.agent.perception.windowhub_form_reader import WindowHubFormReader
        from app.agent.runtime.windowhub_agent_control_loop import (
            create_windowhub_agent_control_loop,
        )
        from app.runtime.execution.robot_action_executor import RobotExecutionMode

        control_loop = create_windowhub_agent_control_loop(plan_reasoner=None)
        mode = _robot_execution_mode(control_loop)
        if mode is not RobotExecutionMode.DRY_RUN:
            raise RuntimeError(f"Expected DRY_RUN execution mode, got {mode!r}.")

        # observe_scene() only observes and perceives; it does not run a plan.
        scene = control_loop.observe_scene()
        observation = scene.observation
        state = observation.state
        metadata = observation.metadata or {}
        title = (state.active_window_title or "").strip()
        root_handle = metadata.get("window_handle")

        if state.active_application != "WindowHub":
            raise RuntimeError(
                f"Unexpected active application label: {state.active_application!r}."
            )
        if not title.casefold().startswith("okna -"):
            raise RuntimeError(
                f"Unexpected WindowHub window title: {title!r}."
            )
        if metadata.get("source") != "windowhub":
            raise RuntimeError(
                f"Unexpected observation source: {metadata.get('source')!r}."
            )
        if not isinstance(root_handle, int) or root_handle <= 0:
            raise RuntimeError("No valid WindowHub window handle was observed.")

        fields = WindowHubFormReader().read(scene)
        uia_raw_field_candidate_census = _uia_raw_field_candidate_census(
            root_handle,
            title,
            metadata.get("window_rect"),
        )
        scene_field_element_census = _scene_field_element_census(
            scene.elements
        )
        document_tab_elements = [
            element
            for element in scene.elements
            if element.kind.casefold() == "tabitem"
            and (element.metadata or {}).get("uia_tab_scope") == "document"
            and isinstance(element.label, str)
            and element.label.strip()
        ]
        document_tab_handles = [
            _positive_handle((element.metadata or {}).get("uia_native_handle"))
            for element in document_tab_elements
        ]
        selected_tab_handles = [
            _positive_handle((element.metadata or {}).get("uia_native_handle"))
            for element in document_tab_elements
            if (element.metadata or {}).get("uia_document_tab_selected") is True
        ]
        selected_document_tab_native_handle = (
            selected_tab_handles[0]
            if len(selected_tab_handles) == 1
            else None
        )
        native_child_windows = _native_child_window_snapshot(root_handle)
        root_client_bounds_screen = _native_client_bounds_screen(root_handle)
        exact_native_document_windows, native_document_window_summary = (
            _native_window_title_matches(
                scene.active_document,
                native_child_windows,
            )
        )
        exact_native_document_window_handles = tuple(
            item["handle"] for item in exact_native_document_windows
        )
        document_tabs = []
        for index, element in enumerate(document_tab_elements):
            handle = document_tab_handles[index]
            other_handles = [
                other
                for other_index, other in enumerate(document_tab_handles)
                if other_index != index and other is not None
            ]
            document_tabs.append({
                "label": element.label,
                "selected": (element.metadata or {}).get(
                    "uia_document_tab_selected"
                ),
                "native_handle_present": handle is not None,
                "native_handle_matches_observed_root": (
                    handle == root_handle
                    if handle is not None and isinstance(root_handle, int)
                    else None
                ),
                "native_handle_shared_with_another_document_tab": (
                    handle in other_handles if handle is not None and other_handles else (
                        False if handle is not None else None
                    )
                ),
            })

        result = {
            "result": "PASS",
            "window_title": title,
            "window_handle_present": True,
            "window_focused": bool(metadata.get("window_focused")),
            "execution_mode": "DRY_RUN",
            "active_document_resolved": bool(scene.active_document),
            "active_document_label": scene.active_document,
            "active_document_resolution": scene.metadata.get(
                "active_document_resolution"
            ),
            "document_tab_count": scene.metadata.get("document_tab_count", 0),
            "selected_document_tab_count": scene.metadata.get(
                "selected_document_tab_count", 0
            ),
            "document_tabs": document_tabs,
            "native_document_window_probe": native_document_window_summary,
            "native_document_window_geometry_probe": (
                _native_document_window_geometry_summary(
                    exact_native_document_windows
                )
            ),
            "coordinate_origin_probe_available_field_count": sum(
                _field_coordinate_origin_probe(
                    field,
                    exact_active_document_windows=exact_native_document_windows,
                    root_window_rect=metadata.get("window_rect"),
                    root_client_bounds_screen=root_client_bounds_screen,
                )["available"] is True
                for field in fields
            ),
            "coordinate_origin_candidate_intersection_counts": {
                candidate: sum(
                    _field_coordinate_origin_probe(
                        field,
                        exact_active_document_windows=exact_native_document_windows,
                        root_window_rect=metadata.get("window_rect"),
                        root_client_bounds_screen=root_client_bounds_screen,
                    )[candidate] is True
                    for field in fields
                )
                for candidate in (
                    "root_relative_intersects",
                    "screen_relative_intersects",
                    "root_client_relative_intersects",
                )
            },
            "uia_raw_field_candidate_census": uia_raw_field_candidate_census,
            "scene_field_element_census": scene_field_element_census,
            "readable_form_field_count": len(fields),
            "field_scope_diagnostics": [
                _field_diagnostic(
                    field,
                    root_handle=root_handle,
                    active_document=scene.active_document,
                    selected_document_tab_native_handle=(
                        selected_document_tab_native_handle
                    ),
                    exact_active_document_window_handles=(
                        exact_native_document_window_handles
                    ),
                    native_child_window_probe_available=(
                        native_child_windows is not None
                    ),
                    exact_active_document_windows=(
                        exact_native_document_windows
                    ),
                    observed_root_window_rect=metadata.get("window_rect"),
                )
                for field in fields
            ],
            "gui_actions_executed": 0,
            "planner_calls": 0,
            "remote_reasoning_calls": 0,
            "field_values_printed": 0,
            "submission_or_save_attempted": 0,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    except Exception as exc:
        print(f"result: FAIL ({type(exc).__name__}: {exc})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
