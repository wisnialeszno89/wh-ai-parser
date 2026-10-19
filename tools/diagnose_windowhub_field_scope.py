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


def _field_diagnostic(
    field,
    *,
    root_handle=None,
    native_relationships=None,
    active_document=None,
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
        "owned_modal": metadata.get("uia_owned_modal") is True,
        "active_document_ancestor_name_exact_match": ancestor_name_exact_match,
        "active_document_window_ancestor_name_exact_match": (
            window_ancestor_name_exact_match
        ),
        "named_window_ancestor_count": named_window_ancestor_count,
        "current_value_present": (
            isinstance(current_value, str) and bool(current_value.strip())
        ),
        "ancestor_structure": ancestry,
    }


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
        document_tabs = [
            {
                "label": element.label,
                "selected": (element.metadata or {}).get(
                    "uia_document_tab_selected"
                ),
            }
            for element in scene.elements
            if element.kind.casefold() == "tabitem"
            and (element.metadata or {}).get("uia_tab_scope") == "document"
            and isinstance(element.label, str)
            and element.label.strip()
        ]

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
            "readable_form_field_count": len(fields),
            "field_scope_diagnostics": [
                _field_diagnostic(
                    field,
                    root_handle=root_handle,
                    active_document=scene.active_document,
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
