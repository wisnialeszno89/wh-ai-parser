"""Redacted, read-only diagnostics for WindowHub UIA grid discovery.

Prints aggregate counts only. Never emits window/document captions, element
labels, AutomationIds, runtime IDs, cell labels, or cell values. No input
actions, task planning, network calls, or persisted screenshots are performed.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _control_type(item, provider) -> str:
    try:
        return provider._normalize_control_type(
            getattr(item.element_info, "control_type", None)
        )
    except Exception:
        return ""


def _grid_dimensions(item):
    """Return GridPattern dimensions, never any row/cell content."""
    try:
        interface = getattr(item, "iface_grid")
        rows = int(interface.CurrentRowCount)
        columns = int(interface.CurrentColumnCount)
        if rows < 0 or columns < 0:
            return None
        return rows, columns
    except Exception:
        return None


def _summarize_grid_candidates(items, provider) -> dict[str, int]:
    type_candidates = 0
    pattern_interfaces = 0
    nonempty_grids = 0
    max_rows = 0
    max_columns = 0

    for item in items:
        control_type = _control_type(item, provider)
        if control_type in {"datagrid", "table"}:
            type_candidates += 1
        dimensions = _grid_dimensions(item)
        if dimensions is None:
            continue
        pattern_interfaces += 1
        rows, columns = dimensions
        if rows > 0 and columns > 0:
            nonempty_grids += 1
            max_rows = max(max_rows, rows)
            max_columns = max(max_columns, columns)

    return {
        "datagrid_or_table_controls": type_candidates,
        "grid_pattern_interfaces": pattern_interfaces,
        "grid_pattern_nonempty_grids": nonempty_grids,
        "max_grid_rows": max_rows,
        "max_grid_columns": max_columns,
    }


def main() -> int:
    if os.name != "nt":
        print("diagnostic_status: unsupported_platform")
        return 2

    try:
        # Reuse the existing strictly read-only, unique-window selection.
        from diagnose_windowhub_semantics import observe_windowhub_scene
        from app.agent.perception.windowhub_ui_automation_provider import (
            WindowHubUIAutomationProvider,
        )

        scene, _, _, stop_reason = observe_windowhub_scene(
            window_title_contains="Okna -"
        )
        if scene is None or stop_reason is not None:
            print("diagnostic_status: window_not_uniquely_observed")
            print("window_selection_failed: True")
            return 2

        observation = scene.observation
        provider = WindowHubUIAutomationProvider()
        desktop = provider._default_desktop()
        window = provider._active_window(
            desktop,
            observation,
            allow_test_factory_fallback=False,
        )
        descendants = tuple(window.descendants())

        control_types: dict[str, int] = {}
        for item in descendants:
            control_type = _control_type(item, provider)
            if control_type in {
                "tabitem", "window", "pane", "datagrid", "table",
                "custom", "list", "listitem", "dataitem",
            }:
                control_types[control_type] = control_types.get(control_type, 0) + 1

        document_tab_items = []
        for item in descendants:
            if _control_type(item, provider) != "tabitem":
                continue
            try:
                if provider._tab_scope(item) == "document":
                    document_tab_items.append(item)
            except Exception:
                continue

        document_tabs_named = 0
        selected_document_tabs = 0
        for item in document_tab_items:
            try:
                name = provider._string(getattr(item.element_info, "name", None))
            except Exception:
                name = None
            if name:
                document_tabs_named += 1
                try:
                    if provider._selection_state(item) is True:
                        selected_document_tabs += 1
                except Exception:
                    pass

        mdi_child_windows = sum(
            1
            for item in descendants
            if _control_type(item, provider) == "window"
            and provider._grid_parent_is_mdi_client(item)
        )
        matched_documents = provider._matched_mdi_document_windows(descendants)

        matched_descendants = []
        matched_subtrees_readable = 0
        for _, _, child_window in matched_documents:
            try:
                child_descendants = tuple(child_window.descendants())
            except Exception:
                continue
            matched_subtrees_readable += 1
            matched_descendants.extend(child_descendants)

        all_candidate_summary = _summarize_grid_candidates(descendants, provider)
        matched_candidate_summary = _summarize_grid_candidates(
            matched_descendants, provider
        )

        # Ask the actual WindowHub provider to run its normal discovery path.
        # Only aggregate markers are retained; no labels or values are printed.
        emitted_elements = provider.perceive(observation)
        emitted_grid_cells = sum(
            1
            for element in emitted_elements
            if (element.metadata or {}).get("uia_grid_cell_observation") is True
        )

        print("diagnostic_status: completed")
        print("mode: READ_ONLY")
        print("computer_actions_executed: 0")
        print("planner_calls: 0")
        print("network_calls_made: 0")
        print("window_selected_uniquely: True")
        print(f"uia_descendants: {len(descendants)}")
        print(f"document_tabitems_by_provider_structure: {len(document_tab_items)}")
        print(f"document_tabs_with_name: {document_tabs_named}")
        print(f"selected_document_tabs_by_uia: {selected_document_tabs}")
        print(f"mdi_client_child_windows: {mdi_child_windows}")
        print(f"matched_tab_to_mdi_documents: {len(matched_documents)}")
        print(f"matched_document_subtrees_readable: {matched_subtrees_readable}")
        print("root_control_type_counts: " + json.dumps(control_types, sort_keys=True))
        print("root_grid_candidates: " + json.dumps(all_candidate_summary, sort_keys=True))
        print("matched_document_grid_candidates: " + json.dumps(matched_candidate_summary, sort_keys=True))
        print(f"provider_emitted_grid_cell_observations: {emitted_grid_cells}")
        print("document_captions_printed: 0")
        print("element_labels_printed: 0")
        print("cell_values_printed: 0")
        return 0
    except Exception as exc:
        # Exception messages can contain application text; expose only type.
        print("diagnostic_status: failed")
        print(f"error_type: {type(exc).__name__}")
        print("error_details_printed: 0")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
