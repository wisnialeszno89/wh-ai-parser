"""Read-only diagnostic for WindowHub form-field document scope.

Prints semantic labels and UI Automation structure only. It never prints
control values, invokes the planner, or executes a GUI action.
"""
from __future__ import annotations

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


def _field_diagnostic(field, *, root_handle=None):
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

    return {
        "label": field.label,
        "control_type": field.control_type,
        "document_scope": field.document_scope,
        "scope_status": field.scope_status,
        "uia_tab_scope": metadata.get("uia_tab_scope"),
        "uia_document_tab_selected": metadata.get(
            "uia_document_tab_selected"
        ),
        "in_observed_root_window": (
            root_handle is not None and observed_handle == root_handle
        ),
        "owned_modal": metadata.get("uia_owned_modal") is True,
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
                _field_diagnostic(field, root_handle=root_handle)
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
