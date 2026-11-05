"""Bridge a NaviMind V2 decision to the existing verified Windows control loop.

NaviMind sees semantic controls, not HWND/RuntimeId or coordinates.
The local runtime owns the native target and checks every postcondition.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

from app.agent.agent_action import AgentAction
from app.agent.agent_intent import AgentIntent
from app.agent.agent_request import AgentRequest
from app.agent.perception.semantic_target_query import SemanticTargetQuery
from app.agent.planning.action_plan import ActionPlan
from app.agent.planning.action_step import ActionStep
from app.agent.runtime.execution_context import ExecutionContext
from app.agent.verification.expected_outcome import ExpectedOutcome
from app.agent.verification.outcome_verifier import OutcomeVerifier


_ALLOWED_STATE_FIELDS = frozenset({"uia_checked", "uia_selected", "uia_focused"})
_GENERIC_LABELS = frozenset({"oknawpf", "lookupedit", "part_item", "layoutcontrol"})


def verified_v2_outcome(resolved, *, baseline_scene=None) -> ExpectedOutcome:
    """Translate a provider-neutral postcondition into a checkable local one."""
    action = resolved.action
    target = action.target
    post = resolved.expected_postcondition
    if not isinstance(post, Mapping):
        raise ValueError("v2_postcondition_required")
    kind = post.get("kind")
    common = {"expected_active_application": "Okna.exe"}
    baseline = OutcomeVerifier._scene_signature(baseline_scene) if baseline_scene is not None else None

    if action.name == "write_text":
        if kind != "entity_value_equals" or post.get("target_ref") != resolved.target_ref:
            raise ValueError("v2_text_requires_exact_value_postcondition")
        if not isinstance(action.value, str) or post.get("expected_value") != action.value:
            raise ValueError("v2_write_expected_value_mismatch")
        if not isinstance(target, SemanticTargetQuery):
            raise ValueError("v2_write_requires_uia_identity")
        return ExpectedOutcome(
            description="The exact edited control contains the intended value.",
            expected_element_label=target.label,
            expected_element_current_value=action.value,
            expected_element_uia_runtime_id=target.uia_runtime_id,
            expected_element_automation_id=target.automation_id,
            **common,
        )

    if action.name == "click_screen_element":
        if not isinstance(target, SemanticTargetQuery):
            raise ValueError("v2_click_requires_uia_identity")
        if kind == "scene_changed":
            return ExpectedOutcome(
                description="The semantic WindowHub scene changed after click.",
                require_scene_change=True,
                baseline_scene_signature=baseline,
                **common,
            )
        if kind == "entity_state_equals":
            if post.get("target_ref") != resolved.target_ref:
                raise ValueError("v2_state_target_mismatch")
            field = post.get("state")
            value = post.get("expected_value")
            if field not in _ALLOWED_STATE_FIELDS or not isinstance(value, bool):
                raise ValueError("v2_unverifiable_state")
            return ExpectedOutcome(
                description="The clicked UIA state matches expected state.",
                expected_element_label=target.label,
                expected_element_uia_runtime_id=target.uia_runtime_id,
                expected_element_automation_id=target.automation_id,
                expected_element_state_name=field,
                expected_element_state_value=value,
                **common,
            )
        raise ValueError("v2_click_postcondition_not_strong_enough")

    if action.name == "activate_window":
        if kind != "scene_changed":
            raise ValueError("v2_window_activation_requires_scene_change")
        return ExpectedOutcome(
            description="Active window changed after activation.",
            require_scene_change=True,
            baseline_scene_signature=baseline,
        )

    raise ValueError("v2_action_not_supported_in_autopilot")


def enforce_v2_live_policy(scene, resolved, *, approved_persistent=False) -> None:
    """Reject unknown targets, ambiguous semantics and persistence without approval."""
    action = resolved.action
    state = scene.observation.state
    if (state.active_application or "").replace("\\", "/").rsplit("/", 1)[-1].casefold() != "okna.exe":
        raise ValueError("v2_windowhub_not_foreground")
    if action.requires_confirmation and not approved_persistent:
        raise ValueError("v2_persistent_action_needs_operator_approval")
    title = (state.active_window_title or "").strip().casefold()
    label = getattr(action.target, "label", None)
    if (
        action.name == "click_screen_element"
        and title in {"zakładanie nowego klienta", "właściwości dokumentu"}
        and isinstance(label, str)
        and label.strip().casefold() in {"ok", "zapisz", "zatwierdź", "zatwierdz"}
        and not approved_persistent
    ):
        raise ValueError("v2_document_commit_requires_explicit_approval")

    if action.name == "activate_window":
        raise ValueError("v2_window_activation_requires_separate_window_policy")
    target = action.target
    if not isinstance(target, SemanticTargetQuery):
        raise ValueError("v2_semantic_uia_target_required")
    matched = [
        e for e in scene.elements
        if (
            (e.metadata or {}).get("source") in {"windows_ui_automation", "windowhub_ui_automation"}
            and (e.metadata or {}).get("uia_runtime_id") == target.uia_runtime_id
            and (e.metadata or {}).get("automation_id") == target.automation_id
            and e.label == target.label
            and e.kind == target.role
            and (e.metadata or {}).get("uia_visible") is True
            and (e.metadata or {}).get("uia_enabled") is True
        )
    ]
    if len(matched) != 1:
        raise ValueError("v2_target_no_longer_uniquely_observed")
    element = matched[0]
    meta = element.metadata or {}
    if (element.label or "").strip().casefold() in _GENERIC_LABELS and not meta.get("semantic_label"):
        raise ValueError("v2_generic_control_meaning_unknown")
    if action.name == "write_text" and element.kind != "edit":
        raise ValueError("v2_text_target_not_edit")
    verified_v2_outcome(resolved)


def execute_v2_step(loop, scene, resolved, *, approved_persistent=False):
    """Run exactly one model-proposed, locally checked action with verification."""
    enforce_v2_live_policy(scene, resolved, approved_persistent=approved_persistent)
    expected = verified_v2_outcome(resolved, baseline_scene=scene)
    action: AgentAction = resolved.action
    # The standard DecisionEngine always sends confirmation-required actions
    # to manual review. A *separate explicit operator flag* is the approval
    # boundary for this bounded local task, not a provider/model assertion.
    if action.requires_confirmation and approved_persistent:
        action = replace(action, requires_confirmation=False)
    context = ExecutionContext(
        request=AgentRequest(message="Execute one verified semantic WindowHub action")
    )
    context.update_scene(scene)
    context.set_value("expected_outcomes", {action.name: expected})
    plan = ActionPlan(
        intent=AgentIntent.COMPUTER_USE,
        steps=(ActionStep(index=1, action=action),),
        confidence=1.0,
    )
    result = loop.run(plan=plan, context=context)
    execution_loop = result.last_execution_result
    attempt = execution_loop.last_attempt if execution_loop is not None else None
    execution = attempt.execution_result if attempt is not None else None
    verification = attempt.verification_result if attempt is not None else None
    if (
        result.success is not True
        or (getattr(execution, "metadata", None) or {}).get("executed") is not True
        or getattr(verification, "verified", None) is not True
    ):
        raise RuntimeError("v2_action_executed_but_not_verified_or_was_blocked")
    return result
