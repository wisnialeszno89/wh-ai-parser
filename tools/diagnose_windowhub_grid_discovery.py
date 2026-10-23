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


def _wrapper_rect(item, provider_module):
    """Get bounds from a pywinauto wrapper without exposing the coordinates."""
    if item is None:
        return None
    try:
        rectangle = item.rectangle()
        return provider_module._UIARect(
            left=int(rectangle.left),
            top=int(rectangle.top),
            width=int(rectangle.width()),
            height=int(rectangle.height()),
        )
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


def _detail_cell_filter_counts(matched_documents, provider) -> dict[str, int]:
    """Mirror the MDI-document viewport filter without exposing UI data."""
    from app.agent.perception import windowhub_ui_automation_provider as provider_module

    counts = {
        "detail_grids_with_valid_rect_and_dimensions": 0,
        "detail_grid_rect_or_pattern_errors": 0,
        "detail_document_or_mdi_rect_errors": 0,
        "detail_cells_requested": 0,
        "detail_getitem_errors": 0,
        "detail_getitem_returned_none": 0,
        "detail_getitem_returned_cell": 0,
        "detail_cell_offscreen_true": 0,
        "detail_cell_offscreen_false": 0,
        "detail_cell_offscreen_unknown": 0,
        "detail_cell_bounds_errors": 0,
        "detail_cells_intersecting_document_window": 0,
        "detail_cells_outside_document_window": 0,
        "detail_cells_intersecting_mdi_client": 0,
        "detail_cells_outside_mdi_client": 0,
        "detail_cells_passing_provider_filters": 0,
        "detail_cell_filter_unexpected_errors": 0,
    }

    for _, _, child_window in matched_documents:
        document_rect = _wrapper_rect(child_window, provider_module)
        mdi_client = provider._grid_parent_item(child_window)
        mdi_rect = _wrapper_rect(mdi_client, provider_module)
        if document_rect is None or mdi_rect is None:
            counts["detail_document_or_mdi_rect_errors"] += 1
            continue

        try:
            document_descendants = tuple(child_window.descendants())
        except Exception:
            counts["detail_grid_rect_or_pattern_errors"] += 1
            continue

        for grid in document_descendants:
            if _control_type(grid, provider) not in {"datagrid", "table"}:
                continue

            try:
                grid_iface = getattr(grid, "iface_grid")
                row_count = int(grid_iface.CurrentRowCount)
                column_count = int(grid_iface.CurrentColumnCount)
                rectangle = grid.rectangle()
                grid_rect = provider_module._UIARect(
                    left=int(rectangle.left),
                    top=int(rectangle.top),
                    width=int(rectangle.width()),
                    height=int(rectangle.height()),
                )
            except Exception:
                counts["detail_grid_rect_or_pattern_errors"] += 1
                continue

            if (
                row_count <= 0 or column_count <= 0
                or grid_rect.width <= 0 or grid_rect.height <= 0
            ):
                continue

            counts["detail_grids_with_valid_rect_and_dimensions"] += 1
            cells_to_read = min(
                row_count * column_count,
                provider.MAX_GRID_CELLS_PER_GRID,
            )
            counts["detail_cells_requested"] += cells_to_read

            for cell_index in range(cells_to_read):
                row = cell_index // column_count
                column = cell_index % column_count
                try:
                    cell = grid_iface.GetItem(row, column)
                except Exception:
                    counts["detail_getitem_errors"] += 1
                    continue
                if cell is None:
                    counts["detail_getitem_returned_none"] += 1
                    continue
                counts["detail_getitem_returned_cell"] += 1

                try:
                    offscreen = provider._uia_cell_offscreen(cell)
                    if offscreen is True:
                        counts["detail_cell_offscreen_true"] += 1
                    elif offscreen is False:
                        counts["detail_cell_offscreen_false"] += 1
                    else:
                        counts["detail_cell_offscreen_unknown"] += 1

                    cell_rect = provider._uia_element_bounds(cell)
                    if cell_rect is None:
                        counts["detail_cell_bounds_errors"] += 1
                        continue

                    in_document = provider._rectangles_intersect(
                        cell_rect, document_rect
                    )
                    if in_document:
                        counts["detail_cells_intersecting_document_window"] += 1
                    else:
                        counts["detail_cells_outside_document_window"] += 1

                    in_mdi_client = provider._rectangles_intersect(
                        cell_rect, mdi_rect
                    )
                    if in_mdi_client:
                        counts["detail_cells_intersecting_mdi_client"] += 1
                    else:
                        counts["detail_cells_outside_mdi_client"] += 1

                    if not in_document or not in_mdi_client:
                        continue

                    legacy = provider._get_grid_pattern(cell, "LegacyIAccessible")
                    name = provider._pattern_string(legacy, "CurrentName")
                    if not name:
                        name = provider._pattern_string(cell, "CurrentName")
                    if not name:
                        continue

                    counts["detail_cells_passing_provider_filters"] += 1
                except Exception:
                    counts["detail_cell_filter_unexpected_errors"] += 1

    return counts


def _per_document_grid_summaries(
    matched_documents,
    document_tab_states: dict[str, bool | None],
    provider,
    root_window=None,
) -> dict[str, dict[str, int]]:
    """Aggregate grid and viewport results separately for selected/hidden MDI docs."""
    summaries = {
        "selected": {},
        "unselected": {},
        "selection_unknown": {},
    }
    counter_names = (
        "matched_documents",
        "viewport_rect_errors",
        "grid_controls",
        "grid_pattern_interfaces",
        "nonempty_grids",
        "cells_requested",
        "getitem_errors",
        "cells_returned",
        "cells_offscreen_true",
        "cell_bounds_errors",
        "cells_intersecting_document_window",
        "cells_outside_document_window",
        "cells_intersecting_mdi_client",
        "cells_outside_mdi_client",
        "cells_passing_name_filter",
    )
    for item in summaries.values():
        item.update({name: 0 for name in counter_names})

    from app.agent.perception import windowhub_ui_automation_provider as provider_module

    for document_key, document_scope, child_window in matched_documents:
        state = document_tab_states.get(document_key)
        bucket = (
            "selected" if state is True
            else "unselected" if state is False
            else "selection_unknown"
        )
        counts = summaries[bucket]
        counts["matched_documents"] += 1

        document_rect = _wrapper_rect(child_window, provider_module)
        mdi_client = provider._grid_parent_item(child_window)
        mdi_rect = _wrapper_rect(mdi_client, provider_module)
        if document_rect is None or mdi_rect is None:
            counts["viewport_rect_errors"] += 1
            continue

        try:
            descendants = tuple(child_window.descendants())
        except Exception:
            continue

        for grid in descendants:
            if _control_type(grid, provider) not in {"datagrid", "table"}:
                continue
            counts["grid_controls"] += 1

            try:
                interface = getattr(grid, "iface_grid")
                row_count = int(interface.CurrentRowCount)
                column_count = int(interface.CurrentColumnCount)
                rectangle = grid.rectangle()
                grid_rect = provider_module._UIARect(
                    left=int(rectangle.left),
                    top=int(rectangle.top),
                    width=int(rectangle.width()),
                    height=int(rectangle.height()),
                )
            except Exception:
                continue

            counts["grid_pattern_interfaces"] += 1
            if row_count <= 0 or column_count <= 0:
                continue
            if grid_rect.width <= 0 or grid_rect.height <= 0:
                continue

            counts["nonempty_grids"] += 1
            cells_to_read = min(
                row_count * column_count,
                provider.MAX_GRID_CELLS_PER_GRID,
            )
            counts["cells_requested"] += cells_to_read

            for cell_index in range(cells_to_read):
                row = cell_index // column_count
                column = cell_index % column_count
                try:
                    cell = interface.GetItem(row, column)
                except Exception:
                    counts["getitem_errors"] += 1
                    continue
                if cell is None:
                    continue
                counts["cells_returned"] += 1

                if provider._uia_cell_offscreen(cell) is True:
                    counts["cells_offscreen_true"] += 1
                cell_rect = provider._uia_element_bounds(cell)
                if cell_rect is None:
                    counts["cell_bounds_errors"] += 1
                    continue

                in_document = provider._rectangles_intersect(
                    cell_rect, document_rect
                )
                if in_document:
                    counts["cells_intersecting_document_window"] += 1
                else:
                    counts["cells_outside_document_window"] += 1

                in_mdi_client = provider._rectangles_intersect(
                    cell_rect, mdi_rect
                )
                if in_mdi_client:
                    counts["cells_intersecting_mdi_client"] += 1
                else:
                    counts["cells_outside_mdi_client"] += 1

                if not in_document or not in_mdi_client:
                    continue

                legacy = provider._get_grid_pattern(cell, "LegacyIAccessible")
                name = provider._pattern_string(legacy, "CurrentName")
                if not name:
                    name = provider._pattern_string(cell, "CurrentName")
                if name:
                    counts["cells_passing_name_filter"] += 1

    return summaries


def main() -> int:
    if os.name != "nt":
        print("diagnostic_status: unsupported_platform")
        return 2

    try:
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
        tab_states_by_key: dict[str, list[bool | None]] = {}
        for item in document_tab_items:
            try:
                name = provider._string(getattr(item.element_info, "name", None))
            except Exception:
                name = None
            if name:
                document_tabs_named += 1
                key = provider._normalized_document_key(name)
                state = provider._selection_state(item)
                tab_states_by_key.setdefault(key, []).append(state)
                if state is True:
                    selected_document_tabs += 1

        # A caption is usable for selected/unselected attribution only when
        # exactly one document-tab item carries that normalized identity.
        document_tab_states: dict[str, bool | None] = {
            key: states[0] if len(states) == 1 else None
            for key, states in tab_states_by_key.items()
        }

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
        detailed_cell_counts = _detail_cell_filter_counts(matched_documents, provider)
        per_document_grid_summaries = _per_document_grid_summaries(
            matched_documents,
            document_tab_states,
            provider,
            root_window=window,
        )

        # Run actual provider discovery too; report only number of emitted cell
        # observations, never captions, labels, values, coordinates or IDs.
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
        print("cell_filter_counts: " + json.dumps(detailed_cell_counts, sort_keys=True))
        print("per_document_grid_summaries: " + json.dumps(per_document_grid_summaries, sort_keys=True))
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
