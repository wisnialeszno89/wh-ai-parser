"""Closed-loop V2 runtime for application-neutral Windows desktop computer use."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
from uuid import uuid4

from app.agent.agent_action import AgentAction
from app.agent.agent_intent import AgentIntent
from app.agent.bridge.agent_task_contract_v2 import (
    validate_agent_task_v2_response,
)
from app.agent.agent_request import AgentRequest
from app.agent.perception.screen_scene import ScreenScene
from app.agent.planning.action_plan import ActionPlan
from app.agent.planning.action_step import ActionStep
from app.agent.runtime.computer_use_v2_action_session import (
    ComputerUseV2ActionSession,
    PreparedComputerUseV2Cycle,
    ResolvedComputerUseV2Action,
)
from app.agent.runtime.execution_context import ExecutionContext
from app.agent.verification.expected_outcome import ExpectedOutcome
from app.agent.verification.expectation_resolver import ExpectationResolver


_SUPPORTED_ELEMENT_STATES = frozenset(
    {
        "uia_selected",
        "uia_focused",
        "uia_enabled",
        "uia_visible",
        "current_value",
        "interaction_capability",
        "kind",
        "label",
    }
)


@dataclass(frozen=True)
class ComputerUseV2CycleResult:
    """A concise, user-safe record of one observation/reason/action cycle."""

    cycle: int
    decision: str
    rationale: str
    action_name: str | None = None
    target: str | None = None
    executed: bool = False
    verified: bool | None = None
    reason: str = ""


@dataclass(frozen=True)
class WindowsDesktopV2RunResult:
    task_id: str
    session_id: str | None
    cycles: tuple[ComputerUseV2CycleResult, ...]
    success: bool
    completed: bool
    requires_manual_review: bool
    stopped: bool
    reason: str


class WindowsDesktopV2AgentRuntime:
    """Observe, reason, perform one action, verify, and observe again."""

    def __init__(
        self,
        *,
        control_loop: AgentControlLoop,
        reasoner,
        action_session: ComputerUseV2ActionSession | None = None,
        experience_provider=None,
    ) -> None:
        if (
            not callable(getattr(control_loop, "observe_scene", None))
            or not callable(getattr(control_loop, "run", None))
        ):
            raise TypeError("windows_desktop_v2_control_loop_invalid")
        if not callable(getattr(reasoner, "reason", None)):
            raise TypeError("windows_desktop_v2_reasoner_invalid")
        self.control_loop = control_loop
        self.reasoner = reasoner
        self.action_session = action_session or ComputerUseV2ActionSession()
        self.experience_provider = experience_provider

    def run(
        self,
        goal: str,
        *,
        max_cycles: int = 20,
        task_id: str | None = None,
        session_id: str | None = None,
    ) -> WindowsDesktopV2RunResult:
        if not isinstance(goal, str) or not goal.strip():
            raise ValueError("computer_use_v2_goal_required")
        if isinstance(max_cycles, bool) or not 1 <= max_cycles <= 100:
            raise ValueError("computer_use_v2_max_cycles_invalid")

        resolved_task_id = task_id or f"desktop-task-{uuid4().hex}"
        resolved_session_id = session_id or f"desktop-session-{uuid4().hex}"
        cycle_results: list[ComputerUseV2CycleResult] = []

        for cycle in range(max_cycles):
            try:
                scene = self.control_loop.observe_scene()
                experience = self._retrieve_experience(scene, goal)
                prepared = self.action_session.prepare_cycle(
                    scene,
                    task_id=resolved_task_id,
                    goal=goal,
                    world_revision=cycle,
                    session_id=resolved_session_id,
                    cycle=cycle,
                    max_cycles=max_cycles,
                    experience=experience,
                )
            except Exception as exc:
                return self._result(
                    resolved_task_id,
                    resolved_session_id,
                    cycle_results,
                    reason=f"observation_or_preparation_failed:{type(exc).__name__}",
                    stopped=True,
                    manual=True,
                )

            response = self.reasoner.reason(prepared.request_payload)
            if response is None:
                reason = getattr(self.reasoner, "last_error", None)
                return self._result(
                    resolved_task_id,
                    resolved_session_id,
                    cycle_results,
                    reason=str(reason or "navimind_v2_returned_no_decision"),
                    stopped=True,
                    manual=True,
                )

            try:
                validate_agent_task_v2_response(
                    response,
                    prepared.request_payload,
                )
            except (TypeError, ValueError) as exc:
                cycle_results.append(
                    ComputerUseV2CycleResult(
                        cycle=cycle,
                        decision="invalid",
                        rationale="",
                        reason=f"invalid_v2_decision:{str(exc)[:160]}",
                    )
                )
                return self._result(
                    resolved_task_id,
                    resolved_session_id,
                    cycle_results,
                    stopped=True,
                    manual=True,
                    reason="invalid_v2_decision",
                )

            decision = response.get("decision")
            rationale = str(response.get("rationale", ""))

            if decision == "done":
                cycle_results.append(
                    ComputerUseV2CycleResult(
                        cycle=cycle,
                        decision="done",
                        rationale=rationale,
                        reason="completion_declared_with_validated_evidence",
                    )
                )
                return self._result(
                    resolved_task_id,
                    resolved_session_id,
                    cycle_results,
                    success=True,
                    completed=True,
                    reason="task_completed_by_navimind_v2",
                )

            if decision == "manual_review":
                cycle_results.append(
                    ComputerUseV2CycleResult(
                        cycle=cycle,
                        decision="manual_review",
                        rationale=rationale,
                        reason="navimind_requested_manual_review",
                    )
                )
                return self._result(
                    resolved_task_id,
                    resolved_session_id,
                    cycle_results,
                    stopped=True,
                    manual=True,
                    reason="navimind_requested_manual_review",
                )

            if decision != "act":
                cycle_results.append(
                    ComputerUseV2CycleResult(
                        cycle=cycle,
                        decision=str(decision),
                        rationale=rationale,
                        reason="unsupported_v2_decision_for_desktop_runtime",
                    )
                )
                return self._result(
                    resolved_task_id,
                    resolved_session_id,
                    cycle_results,
                    stopped=True,
                    manual=True,
                    reason="unsupported_v2_decision_for_desktop_runtime",
                )

            try:
                resolved = prepared.resolve_action_decision(response)
                expected = self._expected_outcome(
                    resolved,
                    prepared,
                    scene,
                )
            except (TypeError, ValueError, KeyError) as exc:
                cycle_results.append(
                    ComputerUseV2CycleResult(
                        cycle=cycle,
                        decision="act",
                        rationale=rationale,
                        reason=f"local_action_validation_failed:{str(exc)[:160]}",
                    )
                )
                return self._result(
                    resolved_task_id,
                    resolved_session_id,
                    cycle_results,
                    stopped=True,
                    manual=True,
                    reason="local_action_validation_failed",
                )

            if resolved.action.requires_confirmation:
                cycle_results.append(
                    ComputerUseV2CycleResult(
                        cycle=cycle,
                        decision="act",
                        rationale=rationale,
                        action_name=resolved.action.name,
                        target=resolved.action.target,
                        reason="explicit_user_confirmation_required",
                    )
                )
                return self._result(
                    resolved_task_id,
                    resolved_session_id,
                    cycle_results,
                    stopped=True,
                    manual=True,
                    reason="explicit_user_confirmation_required",
                )

            context = ExecutionContext(
                request=AgentRequest(
                    message=goal,
                    session_id=resolved_session_id,
                )
            )
            context.update_scene(scene)
            if resolved.action.name == "activate_window":
                try:
                    local_window_handle = int(resolved.action.value)
                except (TypeError, ValueError, OverflowError):
                    return self._result(
                        resolved_task_id,
                        resolved_session_id,
                        cycle_results,
                        stopped=True,
                        manual=True,
                        reason="local_window_activation_binding_invalid",
                    )
                foreground_handle = scene.observation.metadata.get(
                    "foreground_window_handle",
                    scene.observation.metadata.get("window_handle"),
                )
                if (
                    isinstance(foreground_handle, bool)
                    or not isinstance(foreground_handle, int)
                    or foreground_handle <= 0
                    or local_window_handle == foreground_handle
                ):
                    return self._result(
                        resolved_task_id,
                        resolved_session_id,
                        cycle_results,
                        stopped=True,
                        manual=True,
                        reason="local_window_activation_foreground_changed",
                    )
                context.set_value(
                    "_computer_use_v2_window_activation_binding",
                    {
                        "window_handle": local_window_handle,
                        "foreground_window_handle": foreground_handle,
                        "target_ref": resolved.target_ref,
                        "label": resolved.action.target,
                    },
                )
            context.set_value(
                "expected_outcomes",
                {resolved.action.name: expected},
            )

            plan = ActionPlan(
                intent=AgentIntent.COMPUTER_USE,
                steps=(
                    ActionStep(
                        index=1,
                        action=resolved.action,
                    ),
                ),
                confidence=float(response.get("confidence", 0.0)),
            )
            control_result = self.control_loop.run(
                plan=plan,
                context=context,
            )

            execution_loop = control_result.last_execution_result
            attempt = (
                execution_loop.last_attempt
                if execution_loop is not None
                else None
            )
            execution = (
                attempt.execution_result
                if attempt is not None
                else None
            )
            metadata = (
                execution.metadata or {}
                if execution is not None
                else {}
            )
            executed = metadata.get("executed") is True
            verification = (
                attempt.verification_result
                if attempt is not None
                else None
            )
            verified = (
                verification.verified
                if verification is not None
                else None
            )
            reason = (
                verification.reason
                if verification is not None
                else (
                    execution.message
                    if execution is not None
                    else "control_loop_did_not_return_an_execution_attempt"
                )
            )

            cycle_results.append(
                ComputerUseV2CycleResult(
                    cycle=cycle,
                    decision="act",
                    rationale=rationale,
                    action_name=resolved.action.name,
                    target=resolved.action.target,
                    executed=executed,
                    verified=verified,
                    reason=str(reason),
                )
            )

            if not control_result.success:
                return self._result(
                    resolved_task_id,
                    resolved_session_id,
                    cycle_results,
                    stopped=True,
                    manual=control_result.requires_manual_review,
                    reason="action_execution_or_verification_failed",
                )

            if not executed:
                # DRY_RUN must never be mistaken for a completed computer action.
                return self._result(
                    resolved_task_id,
                    resolved_session_id,
                    cycle_results,
                    stopped=True,
                    reason="dry_run_no_hardware_action_performed",
                )

            if verified is not True:
                return self._result(
                    resolved_task_id,
                    resolved_session_id,
                    cycle_results,
                    stopped=True,
                    manual=True,
                    reason="action_postcondition_not_verified",
                )

        return self._result(
            resolved_task_id,
            resolved_session_id,
            cycle_results,
            stopped=True,
            reason="max_cycles_reached_without_completion",
        )

    def _retrieve_experience(
        self,
        scene: ScreenScene,
        goal: str,
    ) -> tuple[Mapping[str, object], ...]:
        """Load a few approved examples for the observed application only."""
        provider = self.experience_provider
        retrieve = getattr(provider, "retrieve", None)
        if not callable(retrieve):
            return ()

        application_id = scene.observation.state.active_application
        if not isinstance(application_id, str) or not application_id.strip():
            return ()
        try:
            records = retrieve(
                application_id=application_id,
                goal=goal,
                max_items=3,
            )
        except Exception:
            # Experience is advisory. An unavailable memory store must not
            # stop a normal desktop task or weaken execution safety.
            return ()

        if not isinstance(records, (tuple, list)):
            return ()
        return tuple(
            dict(record)
            for record in records[:3]
            if isinstance(record, Mapping)
        )

    @staticmethod
    def _expected_outcome(
        resolved: ResolvedComputerUseV2Action,
        prepared: PreparedComputerUseV2Cycle,
        scene: ScreenScene,
    ) -> ExpectedOutcome:
        postcondition = resolved.expected_postcondition
        kind = postcondition.get("kind")

        if kind == "scene_changed":
            return ExpectedOutcome(
                description="The semantic desktop scene changes after the action.",
                require_scene_change=True,
                baseline_scene_signature=(
                    ExpectationResolver._scene_signature(scene)
                ),
            )

        target_ref = postcondition.get("target_ref")
        if not isinstance(target_ref, str):
            raise ValueError("postcondition_target_ref_required")
        target = prepared.snapshot.reference_map.resolve(
            target_ref,
            task_id=prepared.task_id,
            world_revision=prepared.world_revision,
        )
        target_label = target.label.strip() if isinstance(target.label, str) else ""
        if not target_label:
            raise ValueError("postcondition_target_label_missing")

        if kind == "entity_present":
            return ExpectedOutcome(
                description=f"Element '{target_label}' remains present.",
                expected_element_label=target_label,
                element_should_exist=True,
            )

        if kind == "entity_value_equals":
            expected_value = postcondition.get("expected_value")
            if (
                "expected_value_ref" in postcondition
                or not isinstance(expected_value, str)
            ):
                raise ValueError("postcondition_literal_text_value_required")
            return ExpectedOutcome(
                description=f"Element '{target_label}' contains the expected text.",
                expected_element_label=target_label,
                element_should_exist=True,
                expected_element_current_value=expected_value,
            )

        if kind == "entity_state_equals":
            state_name = postcondition.get("state")
            if (
                not isinstance(state_name, str)
                or state_name not in _SUPPORTED_ELEMENT_STATES
                or "expected_value" not in postcondition
            ):
                raise ValueError("postcondition_element_state_unsupported")
            return ExpectedOutcome(
                description=f"Element '{target_label}' reaches the expected state.",
                expected_element_label=target_label,
                expected_element_state_name=state_name,
                expected_element_state_value=postcondition["expected_value"],
            )

        raise ValueError(f"postcondition_not_supported:{kind}")

    @staticmethod
    def _result(
        task_id: str,
        session_id: str,
        cycles: list[ComputerUseV2CycleResult],
        *,
        success: bool = False,
        completed: bool = False,
        manual: bool = False,
        stopped: bool = False,
        reason: str,
    ) -> WindowsDesktopV2RunResult:
        return WindowsDesktopV2RunResult(
            task_id=task_id,
            session_id=session_id,
            cycles=tuple(cycles),
            success=success,
            completed=completed,
            requires_manual_review=manual,
            stopped=stopped,
            reason=reason,
        )
