"""Read-only smoke test against an already-open real WindowHub window.

This diagnostic observes the WindowHub window and semantic UIA controls once.
It does not call the planner, execute a GUI action, print field values, submit
an offer, or use a remote reasoning service.
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
        from app.agent.execution.robot_gui_executor import RobotGUIExecutor
        from app.agent.knowledge.windowhub_offer_knowledge import (
            get_windowhub_offer_knowledge,
        )
        from app.agent.perception.windowhub_form_reader import WindowHubFormReader
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
            raise RuntimeError(
                f"Unexpected active application label: {state.active_application!r}."
            )
        if not window_title.casefold().startswith("okna -"):
            raise RuntimeError(
                "The observed top-level window title does not begin with 'Okna -': "
                f"{window_title!r}."
            )
        if metadata.get("source") != "windowhub":
            raise RuntimeError(
                f"Unexpected observation source: {metadata.get('source')!r}."
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
        print("windowhub_window: PASS")
        print(f"window_title: {window_title}")
        print(f"window_handle_present: {bool(window_handle)}")
        print(f"window_focused: {bool(metadata.get('window_focused'))}")
        print(f"perception_source: {metadata.get('source')}")
        print(f"semantic_controls: {len(elements)}")
        print(f"readable_form_fields: {len(fields)}")
        print(f"active_document_resolved: {bool(scene.active_document)}")
        print("execution_mode: DRY_RUN")
        print("resumable_service: CONFIGURED")
        print("gui_actions_executed: 0")
        print("planner_calls: 0")
        print("remote_reasoning_calls: 0")
        print("field_values_printed: 0")
        print("submission_or_save_attempted: 0")
        print("scope: read-only observation of the real WindowHub window")

        print("semantic_controls_sample:")
        for element in elements[:30]:
            label = (element.label or "").strip() or "<unlabelled>"
            print(f"  - {element.kind}: {label}")
        print("form_field_labels:")
        for field in fields[:30]:
            print(f"  - {field.control_type}: {field.label} [{field.scope_status}]")
        print("result: PASS")
        return 0

    except Exception as exc:
        print(f"result: FAIL ({type(exc).__name__}: {exc})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
