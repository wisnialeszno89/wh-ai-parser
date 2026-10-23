"""Read-only smoke test against an already-open real WindowHub window.

This diagnostic observes the WindowHub window and semantic UIA controls once.
It prints aggregate status/counts only: no window titles, control labels,
field labels, cell labels, or field/cell values are emitted. It does not call
the planner, execute a GUI action, submit an offer, or use remote reasoning.
"""
from __future__ import annotations

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


def main() -> int:
    if os.name != "nt":
        print("FAIL: real WindowHub smoke requires Windows.", file=sys.stderr)
        return 2

    if os.environ.get("WH_REAL_WINDOWHUB", "").strip() == "1":
        print(
            "FAIL: WH_REAL_WINDOWHUB=1 selects LIVE execution. "
            "Unset it before running this read-only smoke.",
            file=sys.stderr,
        )
        return 2

    try:
        from app.agent.knowledge.windowhub_offer_knowledge import (
            get_windowhub_offer_knowledge,
        )
        from app.agent.perception.windowhub_form_reader import WindowHubFormReader
        from app.agent.perception.windowhub_grid_reader import WindowHubGridReader
        from app.agent.bridge.world_state import WorldState
        import json
        from app.agent.runtime.agent_orchestrator import AgentOrchestrator
        from app.agent.runtime.agent_runtime import AgentRuntime
        from app.agent.runtime.windowhub_agent_control_loop import (
            create_windowhub_agent_control_loop,
        )
        from app.runtime.execution.robot_action_executor import RobotExecutionMode

        # Do not configure any reasoning provider: this diagnostic is purely
        # local observation. It intentionally bypasses the task planner.
        control_loop = create_windowhub_agent_control_loop(plan_reasoner=None)
        mode = _robot_execution_mode(control_loop)
        if mode is not RobotExecutionMode.DRY_RUN:
            raise RuntimeError(f"Expected DRY_RUN execution mode, got {mode!r}.")

        runtime = AgentRuntime(
            orchestrator=AgentOrchestrator(
                application_knowledge=get_windowhub_offer_knowledge(),
            ),
            control_loop=control_loop,
        )
        runtime.configure_windowhub_resumable_tasks()

        # The only environment operation performed by this smoke.
        scene = runtime.control_loop.observe_scene()
        observation = scene.observation
        state = observation.state
        metadata = observation.metadata or {}
        window_title = (state.active_window_title or "").strip()
        window_handle = metadata.get("window_handle")

        if state.active_application != "WindowHub":
            raise RuntimeError("Unexpected active application label.")
        if not window_title.casefold().startswith("okna -"):
            raise RuntimeError(
                "Observed top-level window is not a WindowHub window."
            )
        if metadata.get("source") != "windowhub":
            raise RuntimeError(
                "Unexpected observation source."
            )
        if not isinstance(window_handle, int) or window_handle <= 0:
            raise RuntimeError("No valid WindowHub window handle was observed.")

        elements = tuple(scene.elements)
        if not elements:
            raise RuntimeError(
                "The real WindowHub window was found, but no semantic controls "
                "were exposed by perception/UI Automation."
            )

        fields = WindowHubFormReader().read(scene)
        grids = WindowHubGridReader().read_active_document(scene)
        world = WorldState.from_scene(scene)
        world_grid_payloads = world.metadata.get("windowhub_grids", [])
        if not isinstance(world_grid_payloads, list):
            raise RuntimeError("Structured grid payload is not a list.")
        # Ensure the structured world bridge sees exactly the same bounded
        # active-document grid set; never print row labels or cell values.
        expected_payload_count = min(len(grids), 20)
        if len(world_grid_payloads) != expected_payload_count:
            raise RuntimeError(
                "Structured grid payload count does not match the active-document reader."
            )
        json.dumps(world.to_payload(), ensure_ascii=False)

        print("windowhub_window: PASS")
        print("window_title_present: True")
        print(f"window_handle_present: {bool(window_handle)}")
        print(f"window_focused: {bool(metadata.get('window_focused'))}")
        print(f"perception_source: {metadata.get('source')}")
        print(f"semantic_controls: {len(elements)}")
        print(f"readable_form_fields: {len(fields)}")
        scene_meta = getattr(scene, "metadata", {}) or {}
        tab_items = tuple(
            element for element in elements
            if str(getattr(element, "kind", "")).casefold() == "tabitem"
        )
        document_tab_markers = tuple(
            element for element in elements
            if (getattr(element, "metadata", {}) or {}).get("uia_tab_scope") == "document"
        )
        selected_document_tab_markers = tuple(
            element for element in elements
            if (
                (getattr(element, "metadata", {}) or {}).get("uia_tab_scope") == "document"
                and (getattr(element, "metadata", {}) or {}).get("uia_document_tab_selected") is True
            )
        )
        print(f"active_document_resolved: {bool(scene.active_document)}")
        print(f"active_document_resolution: {scene_meta.get('active_document_resolution', 'unknown')}")
        print(f"document_tab_count_from_engine: {scene_meta.get('document_tab_count', 'unknown')}")
        print(f"selected_document_tab_count_from_engine: {scene_meta.get('selected_document_tab_count', 'unknown')}")
        print(f"tabitems_in_fused_scene: {len(tab_items)}")
        print(f"document_tab_markers_in_fused_scene: {len(document_tab_markers)}")
        print(f"selected_document_tab_markers_in_fused_scene: {len(selected_document_tab_markers)}")
        print(f"active_document_grids: {len(grids)}")
        print(f"structured_grid_payloads: {len(world_grid_payloads)}")
        print(
            "grid_observation_complete_count: "
            f"{sum(1 for grid in grids if grid.complete)}"
        )
        for index, grid in enumerate(grids):
            print(
                f"grid_{index}: rows={grid.row_count}, "
                f"columns={grid.column_count}, "
                f"observed_cells={grid.observed_cell_count}, "
                f"missing_cells={grid.missing_cell_count}, "
                f"unreadable_values={grid.unreadable_value_count}, "
                f"complete={grid.complete}, "
                f"truncated={grid.truncated}, "
                f"matrix_omitted={grid.matrix_omitted}"
            )
        print("grid_cell_labels_printed: 0")
        print("grid_cell_values_printed: 0")
        print("grid_provider_ids_printed: 0")
        print("execution_mode: DRY_RUN")
        print("resumable_service: CONFIGURED")
        print("gui_actions_executed: 0")
        print("planner_calls: 0")
        print("remote_reasoning_calls: 0")
        print("field_values_printed: 0")
        print("submission_or_save_attempted: 0")
        print("scope: read-only observation of the real WindowHub window")

        print("semantic_control_labels_printed: 0")
        print("form_field_labels_printed: 0")
        print("grid_cell_labels_printed: 0")
        print("grid_cell_values_printed: 0")
        print("result: PASS")
        return 0

    except Exception as exc:
        print(f"result: FAIL ({type(exc).__name__})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
