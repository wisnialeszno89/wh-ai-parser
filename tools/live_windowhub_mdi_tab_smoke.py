"""Single-action live smoke test for verified WindowHub MDI tab activation.

This test deliberately bypasses task reasoning and invokes the same
RobotGUIExecutor path used by the agent for exactly one semantic target.
It only activates the Start1 document tab; it never enters or saves offer data.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _start1_tabs(scene):
    return [
        element
        for element in tuple(getattr(scene, "elements", ()) or ())
        if (
            str(getattr(element, "label", "") or "").strip().casefold() == "start1"
            and (getattr(element, "metadata", {}) or {}).get("uia_tab_scope") == "document"
            and isinstance(
                (getattr(element, "metadata", {}) or {}).get(
                    "uia_document_tab_selected"
                ),
                bool,
            )
        )
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Perform one verified WindowHub Start1 tab activation through "
            "RobotGUIExecutor and verify the resulting scene."
        )
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Required opt-in for the single live document-tab action.",
    )
    args = parser.parse_args()

    if os.name != "nt":
        print("ABORTED: This live smoke test requires Windows.")
        return 2
    if not args.execute:
        print("ABORTED: Add --execute to authorize the single Start1 tab action.")
        return 2
    if os.environ.get("WH_REAL_WINDOWHUB", "").strip() != "1":
        print("ABORTED: WH_REAL_WINDOWHUB=1 is required for the live action.")
        return 2

    try:
        from app.agent.agent_action import AgentAction
        from app.agent.agent_request import AgentRequest
        from app.agent.execution.robot_gui_executor import RobotGUIExecutor
        from app.agent.runtime.execution_context import ExecutionContext
        from app.agent.runtime.windowhub_agent_control_loop import (
            create_windowhub_agent_control_loop,
        )
        from app.runtime.execution.robot_action_executor import RobotExecutionMode
        from tools.inspect_live_windowhub_ui_targets import _windowhub_hwnd
        from tools.live_click_windowhub_target import _focus_window
    except Exception as exc:
        print(json.dumps({
            "result": "FAIL",
            "phase": "imports",
            "error_type": type(exc).__name__,
            "gui_actions_executed": 0,
        }, ensure_ascii=False, indent=2))
        return 3

    hwnd = _windowhub_hwnd()
    if not hwnd:
        print("ABORTED: No visible WindowHub root window was found.")
        return 3
    if not _focus_window(hwnd):
        print("ABORTED: Windows did not grant foreground status to WindowHub.")
        return 4
    time.sleep(0.25)

    try:
        control_loop = create_windowhub_agent_control_loop(plan_reasoner=None)
        executors = [
            item
            for item in control_loop.verification_loop.execution_engine.registry.all()
            if isinstance(item, RobotGUIExecutor)
        ]
        if len(executors) != 1:
            raise RuntimeError(
                f"Expected exactly one RobotGUIExecutor; found {len(executors)}."
            )
        executor = executors[0]
        if executor.robot_action_executor.mode is not RobotExecutionMode.LIVE:
            raise RuntimeError("The executor is not in LIVE mode.")

        before_scene = control_loop.observe_scene()
        before_tabs = _start1_tabs(before_scene)
        before_selected = (
            (before_tabs[0].metadata or {}).get("uia_document_tab_selected")
            if len(before_tabs) == 1
            else None
        )
        before_active_is_start1 = (
            isinstance(before_scene.active_document, str)
            and before_scene.active_document.strip().casefold() == "start1"
        )

        if len(before_tabs) != 1:
            raise RuntimeError(
                f"Expected exactly one semantic Start1 document tab; found {len(before_tabs)}."
            )
        metadata = before_tabs[0].metadata or {}
        if metadata.get("uia_visible") is not True or metadata.get("uia_enabled") is not True:
            raise RuntimeError("The Start1 tab is not visible and enabled.")
        if not isinstance(before_scene.active_document, str) or not before_scene.active_document.strip():
            raise RuntimeError("The active document is not resolved; refusing to act.")
        if before_selected is True and not before_active_is_start1:
            raise RuntimeError("UIA and active-document state disagree before the action.")
        if before_selected is False and before_active_is_start1:
            raise RuntimeError("UIA and active-document state disagree before the action.")

        request = AgentRequest(
            message="Activate the uniquely identified Start1 document tab.",
            session_id="live-windowhub-mdi-tab-smoke",
            salesman_id="controlled-smoke-test",
            metadata={},
        )
        context = ExecutionContext(
            request=request,
            current_scene=before_scene,
        )
        result = executor.execute(
            AgentAction(
                name="click_screen_element",
                description="Activate the verified Start1 document tab using the WindowHub document-navigation path.",
                target="Start1",
                requires_environment_observation=True,
            ),
            context,
        )

        # Always make a fresh observation, even if the executor reports a
        # failure: an attempted native action must be checked before stopping.
        # Action success alone is not proof that WindowHub changed documents.
        after_scene = control_loop.observe_scene()
        after_tabs = _start1_tabs(after_scene)
        after_selected = (
            (after_tabs[0].metadata or {}).get("uia_document_tab_selected")
            if len(after_tabs) == 1
            else None
        )
        after_active_is_start1 = (
            isinstance(after_scene.active_document, str)
            and after_scene.active_document.strip().casefold() == "start1"
        )
        verified = (
            result.success
            and len(after_tabs) == 1
            and after_selected is True
            and after_active_is_start1
        )

        report = {
            "result": "PASS" if verified else "FAIL",
            "phase": "post_action_verification",
            "executor_reported_success": result.success,
            "active_document_resolved_before": True,
            "start1_selected_before": before_selected,
            "start1_active_before": before_active_is_start1,
            "execution_path": (result.metadata or {}).get("execution_path"),
            "action_executed": (result.metadata or {}).get("executed", False),
            "active_document_is_start1_after": after_active_is_start1,
            "start1_selected_after": after_selected,
            "post_action_state_verified": verified,
            "offer_data_entered": False,
            "offer_saved": False,
            "additional_gui_actions": 0,
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if verified else 6

    except Exception as exc:
        print(json.dumps({
            "result": "FAIL",
            "phase": "safe_execution",
            "error_type": type(exc).__name__,
            "error": "The supervised MDI tab smoke stopped safely; inspect the preceding state report.",
            "offer_data_entered": False,
            "offer_saved": False,
        }, ensure_ascii=False, indent=2))
        return 7


if __name__ == "__main__":
    raise SystemExit(main())
