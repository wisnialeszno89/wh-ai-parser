"""One-action task-reasoner smoke test for opening the WindowHub new-offer dialog.

The reasoner may propose a plan, but the execution guard permits only one
semantic click on the uniquely observed NOWA OFERTA button. The script never
types into the dialog, confirms it, or saves an offer.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


_TARGET_LABELS = frozenset({"nowa oferta"})


class _ReasonedPlanBlocked(RuntimeError):
    """Raised before GUI execution if the reasoner proposes another action."""


def _normalize_label(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.casefold().split()).strip(" .!?;:")


def _metadata(element) -> dict:
    value = getattr(element, "metadata", {}) or {}
    return dict(value) if isinstance(value, dict) else {}


def _label(element) -> str:
    return _normalize_label(getattr(element, "label", None))


def _has_uia_provenance(metadata: dict) -> bool:
    if metadata.get("source") == "windowhub_ui_automation":
        return True
    sources = metadata.get("fusion_sources") or ()
    if isinstance(sources, str):
        return sources == "windowhub_ui_automation"
    try:
        return "windowhub_ui_automation" in sources
    except TypeError:
        return False


def _owned_modal_labels(scene) -> tuple[str, ...]:
    labels = set()
    for element in tuple(getattr(scene, "elements", ()) or ()):
        metadata = _metadata(element)
        if (
            metadata.get("uia_owned_modal") is True
            and metadata.get("uia_visible") is not False
        ):
            label = _label(element)
            if label:
                labels.add(label)
    return tuple(sorted(labels))


def _offer_dialog_detected(scene) -> bool:
    labels = set(_owned_modal_labels(scene))
    return "ok" in labels and "anuluj" in labels


def _start1_activation_problem(scene) -> str | None:
    """Validate a single, bounded attempt to activate the Start1 document tab."""
    if scene is None:
        return "Initial WindowHub scene is unavailable."

    active_document = _normalize_label(
        getattr(scene, "active_document", None)
    )
    if not active_document:
        return "The active document is unresolved; refusing tab activation."

    tabs = [
        element
        for element in tuple(getattr(scene, "elements", ()) or ())
        if (
            _label(element) == "start1"
            and _metadata(element).get("uia_tab_scope") == "document"
        )
    ]
    if len(tabs) != 1:
        return f"Expected one Start1 document tab; found {len(tabs)}."

    metadata = _metadata(tabs[0])
    if metadata.get("uia_visible") is not True:
        return "The Start1 document tab is not confirmed visible."
    if metadata.get("uia_enabled") is not True:
        return "The Start1 document tab is not confirmed enabled."

    capability = getattr(
        getattr(tabs[0], "interaction_capability", None),
        "value",
        getattr(tabs[0], "interaction_capability", None),
    )
    if capability not in {"selectable", "clickable"}:
        return "The Start1 document tab is not exposed as selectable."

    selected = metadata.get("uia_document_tab_selected")
    if selected not in {None, True, False}:
        return "The Start1 tab selection state is malformed."
    if selected is True and active_document != "start1":
        return "UIA selection conflicts with the resolved active document."
    if selected is False and active_document == "start1":
        return "UIA selection conflicts with the resolved active document."

    return None


def _activate_start1_once(control_loop, before_scene) -> dict:
    """Activate Start1 through the normal GUI executor and verify the new scene."""
    from app.agent.agent_action import AgentAction
    from app.agent.agent_request import AgentRequest
    from app.agent.execution.robot_gui_executor import RobotGUIExecutor
    from app.agent.runtime.execution_context import ExecutionContext
    from app.runtime.execution.robot_action_executor import RobotExecutionMode

    problem = _start1_activation_problem(before_scene)
    if problem is not None:
        return {
            "attempted": False,
            "executed": False,
            "verified": False,
            "scene": before_scene,
            "error": problem,
        }

    executors = [
        item
        for item in control_loop.verification_loop.execution_engine.registry.all()
        if isinstance(item, RobotGUIExecutor)
    ]
    if len(executors) != 1:
        return {
            "attempted": False,
            "executed": False,
            "verified": False,
            "scene": before_scene,
            "error": f"Expected exactly one RobotGUIExecutor; found {len(executors)}.",
        }

    executor = executors[0]
    if executor.robot_action_executor.mode is not RobotExecutionMode.LIVE:
        return {
            "attempted": False,
            "executed": False,
            "verified": False,
            "scene": before_scene,
            "error": "The executor is not in LIVE mode.",
        }

    request = AgentRequest(
        message="Activate the uniquely identified Start1 document tab.",
        session_id=f"windowhub-new-offer-start1-{uuid4().hex}",
        salesman_id="controlled-smoke-test",
        metadata={"target_application": "WindowHub"},
    )
    context = ExecutionContext(request=request, current_scene=before_scene)

    result = executor.execute(
        AgentAction(
            name="click_screen_element",
            description="Activate the verified Start1 document tab through the WindowHub MDI navigation path.",
            target="Start1",
            requires_environment_observation=True,
        ),
        context,
    )
    result_metadata = getattr(result, "metadata", {}) or {}
    if not isinstance(result_metadata, dict):
        result_metadata = {}
    executed = result_metadata.get("executed") is True

    if not getattr(result, "success", False) or not executed:
        return {
            "attempted": True,
            "executed": executed,
            "verified": False,
            "scene": before_scene,
            "execution_path": result_metadata.get("execution_path"),
            "error": getattr(result, "message", None) or (
                "The Start1 activation was not confirmed by the executor."
            ),
        }

    after_scene = control_loop.observe_scene()
    after_tabs = [
        element
        for element in tuple(getattr(after_scene, "elements", ()) or ())
        if (
            _label(element) == "start1"
            and _metadata(element).get("uia_tab_scope") == "document"
        )
    ]
    selected_after = (
        _metadata(after_tabs[0]).get("uia_document_tab_selected")
        if len(after_tabs) == 1
        else None
    )
    active_after = _normalize_label(
        getattr(after_scene, "active_document", None)
    ) == "start1"
    verified = (
        len(after_tabs) == 1
        and active_after
        and selected_after is not False
    )

    return {
        "attempted": True,
        "executed": True,
        "verified": verified,
        "scene": after_scene,
        "execution_path": result_metadata.get("execution_path"),
        "active_document_after": getattr(after_scene, "active_document", None),
        "selected_after": selected_after,
        "error": None if verified else (
            "Start1 activation was issued, but the post-action scene did not verify it."
        ),
    }


def _initial_scene_problem(scene) -> str | None:
    if scene is None:
        return "Initial WindowHub scene is unavailable."

    active_document = _normalize_label(
        getattr(scene, "active_document", None)
    )
    if active_document != "start1":
        return (
            "Start1 is not the active document; no action was attempted "
            f"(active_document={getattr(scene, 'active_document', None)!r})."
        )

    elements = tuple(getattr(scene, "elements", ()) or ())
    start_tabs = [
        element
        for element in elements
        if (
            _label(element) == "start1"
            and _metadata(element).get("uia_tab_scope") == "document"
        )
    ]
    if len(start_tabs) != 1:
        return f"Expected one Start1 document tab; found {len(start_tabs)}."

    selected_state = _metadata(start_tabs[0]).get("uia_document_tab_selected")
    if selected_state is False:
        return (
            "Start1 selection conflicts with the resolved active document; "
            "no action attempted."
        )
    if selected_state is not True and selected_state is not None:
        return "Start1 selection state is invalid; no action attempted."

    if _offer_dialog_detected(scene):
        return (
            "A WindowHub-owned dialog with OK and Anuluj is already open; "
            "refusing to start another offer."
        )

    buttons = [
        element
        for element in elements
        if (
            _label(element) in _TARGET_LABELS
            and _metadata(element).get("uia_control_type") == "button"
            and _metadata(element).get("uia_visible") is True
            and _metadata(element).get("uia_enabled") is True
            and _has_uia_provenance(_metadata(element))
            and getattr(
                getattr(element, "interaction_capability", None),
                "value",
                getattr(element, "interaction_capability", None),
            ) == "clickable"
        )
    ]
    if len(buttons) != 1:
        return (
            "Expected one visible, enabled, UIA-grounded NOWA OFERTA button; "
            f"found {len(buttons)}."
        )

    button_scope = _normalize_label(_metadata(buttons[0]).get("document_scope"))
    if button_scope != active_document:
        return (
            "NOWA OFERTA document_scope does not match the active document; "
            "refusing to execute the click."
        )

    return None


def _plan_block_reason(plan) -> str | None:
    if plan is None:
        return "The reasoner returned no plan."
    if bool(getattr(plan, "requires_manual_review", False)):
        return "The proposed plan requires manual review."
    if bool(getattr(plan, "completed", False)):
        return "The reasoner marked the goal complete without an action."

    steps = tuple(getattr(plan, "steps", ()) or ())
    if len(steps) != 1:
        return (
            "The execution guard accepts exactly one action; "
            f"received {len(steps)}."
        )

    action = getattr(steps[0], "action", None)
    if action is None:
        return "The plan step has no semantic action."
    if getattr(action, "name", None) != "click_screen_element":
        return (
            "Blocked non-click action: "
            f"{getattr(action, 'name', None)!r}."
        )
    if _normalize_label(getattr(action, "target", None)) not in _TARGET_LABELS:
        return (
            "Blocked because the planned target is not NOWA OFERTA: "
            f"{getattr(action, 'target', None)!r}."
        )
    value = getattr(action, "value", None)
    if isinstance(value, str) and value.strip():
        return "Blocked click action carrying a text value."
    if bool(getattr(action, "requires_confirmation", False)):
        return "Blocked action that requires confirmation."

    return None


def _execution_details(result) -> dict:
    control = getattr(result, "control_loop_result", None)
    executions = tuple(getattr(control, "execution_results", ()) or ())
    execution_result = None
    verification = None

    if executions:
        attempt = getattr(executions[-1], "last_attempt", None)
        if attempt is not None:
            execution_result = getattr(attempt, "execution_result", None)
            verification = getattr(attempt, "verification_result", None)

    metadata = getattr(execution_result, "metadata", {}) or {}
    if not isinstance(metadata, dict):
        metadata = {}

    return {
        "control_success": getattr(control, "success", None),
        "execution_success": getattr(execution_result, "success", None),
        "action_executed": metadata.get("executed") is True,
        "execution_path": metadata.get("execution_path"),
        "execution_message": getattr(execution_result, "message", None),
        "verification_verified": getattr(verification, "verified", None),
        "verification_reason": getattr(verification, "reason", None),
        "executed_actions": getattr(control, "executed_actions", None),
        "failed_actions": getattr(control, "failed_actions", None),
    }


def _visible_labels(scene, limit: int = 80) -> list[str]:
    labels = []
    for element in tuple(getattr(scene, "elements", ()) or ()):
        label = getattr(element, "label", None)
        if isinstance(label, str) and label.strip():
            metadata = _metadata(element)
            if metadata.get("uia_visible") is not False:
                labels.append(label.strip())
    return list(dict.fromkeys(labels))[:limit]


def main() -> int:
    try:
        from dotenv import load_dotenv
        load_dotenv()

        if os.name != "nt":
            print(json.dumps({
                "result": "ABORTED",
                "phase": "preconditions",
                "error": "This live smoke test requires Windows.",
                "offer_data_entered": False,
                "offer_saved": False,
            }, ensure_ascii=False, indent=2))
            return 2

        if os.environ.get("WH_REAL_WINDOWHUB") != "1":
            print(json.dumps({
                "result": "ABORTED",
                "phase": "preconditions",
                "error": "WH_REAL_WINDOWHUB=1 is required.",
                "offer_data_entered": False,
                "offer_saved": False,
            }, ensure_ascii=False, indent=2))
            return 2

        if os.environ.get("COMPUTER_REAL", "0").strip() != "0":
            print(json.dumps({
                "result": "ABORTED",
                "phase": "preconditions",
                "error": "COMPUTER_REAL must be 0 for this WindowHub-only test.",
                "offer_data_entered": False,
                "offer_saved": False,
            }, ensure_ascii=False, indent=2))
            return 2

        if (
            not os.environ.get("NAVIMIND_AGENT_URL", "").strip()
            and os.environ.get("AGENT_TASK_REASONING") != "1"
        ):
            print(json.dumps({
                "result": "ABORTED",
                "phase": "preconditions",
                "error": "Configure NAVIMIND_AGENT_URL or AGENT_TASK_REASONING=1.",
                "offer_data_entered": False,
                "offer_saved": False,
            }, ensure_ascii=False, indent=2))
            return 2

        from app.agent.agent_request import AgentRequest
        from app.agent.runtime.windowhub_agent_runtime import (
            create_windowhub_agent_runtime,
        )
        from tools.inspect_live_windowhub_ui_targets import _windowhub_hwnd, _window_title
        from tools.live_click_windowhub_target import _focus_window

        hwnd = _windowhub_hwnd()
        if not hwnd:
            print(json.dumps({
                "result": "ABORTED",
                "phase": "preconditions",
                "error": "No visible WindowHub root window was found.",
                "offer_data_entered": False,
                "offer_saved": False,
            }, ensure_ascii=False, indent=2))
            return 3
        if not _focus_window(hwnd):
            print(json.dumps({
                "result": "ABORTED",
                "phase": "preconditions",
                "error": "WindowHub could not be focused.",
                "offer_data_entered": False,
                "offer_saved": False,
            }, ensure_ascii=False, indent=2))
            return 4

        time.sleep(0.35)
        runtime = create_windowhub_agent_runtime()
        control_loop = runtime.control_loop
        if control_loop is None:
            raise RuntimeError("WindowHub control loop is not configured.")

        task_planner = getattr(runtime.orchestrator, "task_planner", None)
        reasoner = getattr(task_planner, "reasoner", None)
        if reasoner is None:
            print(json.dumps({
                "result": "ABORTED",
                "phase": "reasoner",
                "error": "No task reasoner is configured; refusing fallback planning.",
                "offer_data_entered": False,
                "offer_saved": False,
            }, ensure_ascii=False, indent=2))
            return 5

        before_scene = control_loop.observe_scene()
        active_document_before_any_action = getattr(
            before_scene,
            "active_document",
            None,
        )
        start1_activation = {
            "attempted": False,
            "executed": False,
            "verified": _normalize_label(active_document_before_any_action) == "start1",
            "scene": before_scene,
            "error": None,
        }

        # Do not ask the user to manually repeat tab selection. If Start1 is
        # not active, perform exactly one guarded MDI-tab activation, verify
        # the new scene, then continue to the existing one-click offer flow.
        if _normalize_label(active_document_before_any_action) != "start1":
            start1_activation = _activate_start1_once(
                control_loop,
                before_scene,
            )
            if not start1_activation["verified"]:
                print(json.dumps({
                    "result": "ABORTED",
                    "phase": "start1_activation",
                    "error": start1_activation.get("error"),
                    "active_document_before": active_document_before_any_action,
                    "active_document_after": start1_activation.get("active_document_after"),
                    "start1_activation_attempted": start1_activation["attempted"],
                    "start1_activation_executed": start1_activation["executed"],
                    "start1_activation_verified": False,
                    "execution_path": start1_activation.get("execution_path"),
                    "offer_data_entered": False,
                    "offer_saved": False,
                    "gui_actions_executed": 1 if start1_activation["executed"] else 0,
                    "offer_click_executed": False,
                }, ensure_ascii=False, indent=2))
                return 5
            before_scene = start1_activation["scene"]

        scene_problem = _initial_scene_problem(before_scene)
        if scene_problem is not None:
            print(json.dumps({
                "result": "ABORTED",
                "phase": "preconditions",
                "error": scene_problem,
                "active_document_before": active_document_before_any_action,
                "active_document_before_offer_click": getattr(before_scene, "active_document", None),
                "start1_activation_attempted": start1_activation["attempted"],
                "start1_activation_executed": start1_activation["executed"],
                "start1_activation_verified": start1_activation["verified"],
                "offer_data_entered": False,
                "offer_saved": False,
                "gui_actions_executed": 1 if start1_activation["executed"] else 0,
                "offer_click_executed": False,
            }, ensure_ascii=False, indent=2))
            return 5

        # One verification pass only. The runtime is also called with
        # autonomous=True, which truncates the plan to its first semantic step.
        control_loop.verification_loop.max_attempts = 1
        original_run = control_loop.run
        guard_state = {"allowed_action": None, "called": False}

        def guarded_run(*, plan, context):
            reason = _plan_block_reason(plan)
            if reason is not None:
                raise _ReasonedPlanBlocked(reason)
            action = plan.steps[0].action
            guard_state["allowed_action"] = {
                "name": action.name,
                "target": action.target,
                "description": action.description,
            }
            guard_state["called"] = True
            return original_run(plan=plan, context=context)

        control_loop.run = guarded_run

        request = AgentRequest(
            message="Otwórz nową ofertę",
            session_id=f"windowhub-new-offer-open-smoke-{uuid4().hex}",
            salesman_id="controlled-smoke-test",
            metadata={
                "disable_learned_workflow_replay": True,
                "target_application": "WindowHub",
            },
        )

        try:
            result = runtime.run(request, autonomous=True)
        except _ReasonedPlanBlocked as exc:
            print(json.dumps({
                "result": "BLOCKED",
                "phase": "reasoner_plan_guard",
                "reason": str(exc),
                "task_reasoner": type(reasoner).__name__,
                "planned_action": guard_state.get("allowed_action"),
                "action_executed": False,
                "start1_activation_executed": start1_activation["executed"],
                "start1_activation_verified": start1_activation["verified"],
                "offer_data_entered": False,
                "offer_saved": False,
                "gui_actions_executed": 1 if start1_activation["executed"] else 0,
                "offer_click_executed": False,
            }, ensure_ascii=False, indent=2))
            return 6

        planned_action = guard_state.get("allowed_action")
        if not guard_state["called"]:
            plan = getattr(getattr(result, "context", None), "plan", None)
            steps = tuple(getattr(plan, "steps", ()) or ())
            candidate = None
            if steps:
                action = getattr(steps[0], "action", None)
                if action is not None:
                    candidate = {
                        "name": getattr(action, "name", None),
                        "target": getattr(action, "target", None),
                        "description": getattr(action, "description", None),
                    }
            print(json.dumps({
                "result": "BLOCKED",
                "phase": "reasoner",
                "error": getattr(
                    getattr(result, "context", None),
                    "get_value",
                    lambda *_args, **_kwargs: None,
                )("task_reasoning_failure", None),
                "task_reasoner": type(reasoner).__name__,
                "reasoned_plan_candidate": candidate,
                "action_executed": False,
                "start1_activation_executed": start1_activation["executed"],
                "start1_activation_verified": start1_activation["verified"],
                "offer_data_entered": False,
                "offer_saved": False,
                "gui_actions_executed": 1 if start1_activation["executed"] else 0,
                "offer_click_executed": False,
            }, ensure_ascii=False, indent=2))
            return 6

        # A fresh observation is read-only. The guarded runtime has executed
        # only one click, and is never asked to continue the workflow.
        after_scene = control_loop.observe_scene()
        details = _execution_details(result)
        modal_labels = list(_owned_modal_labels(after_scene))
        dialog_detected = _offer_dialog_detected(after_scene)
        after_active_document = getattr(after_scene, "active_document", None)
        report = {
            "result": (
                "PASS"
                if (
                    details["action_executed"]
                    and details["execution_success"] is True
                    and dialog_detected
                )
                else "FAIL"
            ),
            "phase": "post_action_verification",
            "windowhub_title": _window_title(hwnd),
            "task_reasoner": type(reasoner).__name__,
            "planned_action": planned_action,
            "active_document_before": active_document_before_any_action,
            "active_document_before_offer_click": getattr(before_scene, "active_document", None),
            "active_document_after": after_active_document,
            "start1_activation_attempted": start1_activation["attempted"],
            "start1_activation_executed": start1_activation["executed"],
            "start1_activation_verified": start1_activation["verified"],
            "execution_path": details["execution_path"],
            "execution_success": details["execution_success"],
            "action_executed": details["action_executed"],
            "verification_verified": details["verification_verified"],
            "verification_reason": details["verification_reason"],
            "owned_modal_labels_after": modal_labels,
            "new_offer_dialog_detected": dialog_detected,
            "observed_labels_after": _visible_labels(after_scene),
            "offer_data_entered": False,
            "offer_saved": False,
            "gui_actions_allowed": 2,
            "gui_actions_executed": (
                (1 if start1_activation["executed"] else 0)
                + (1 if details["action_executed"] else 0)
            ),
            "offer_click_executed": details["action_executed"],
            "additional_gui_actions": 0,
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["result"] == "PASS" else 7

    except Exception as exc:
        print(json.dumps({
            "result": "FAIL",
            "phase": "safe_execution",
            "error_type": type(exc).__name__,
            "error": "The bounded WindowHub smoke stopped. No follow-up action is attempted.",
            "start1_activation_executed": (
                start1_activation.get("executed", False)
                if "start1_activation" in locals()
                else False
            ),
            "offer_click_executed": False,
            "gui_actions_executed": (
                1 if (
                    "start1_activation" in locals()
                    and start1_activation.get("executed", False)
                ) else 0
            ),
            "offer_data_entered": False,
            "offer_saved": False,
        }, ensure_ascii=False, indent=2))
        return 8


if __name__ == "__main__":
    raise SystemExit(main())
