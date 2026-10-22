"""WindowHub adapter for the durable, one-action-at-a-time task runner."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from decimal import Decimal, InvalidOperation
import json
import re
import unicodedata

from app.agent.agent_action import AgentAction
from app.agent.agent_intent import AgentIntent
from app.agent.agent_request import AgentRequest
from app.agent.knowledge.windowhub_offer_knowledge import (
    get_windowhub_offer_knowledge,
)
from app.agent.perception.target_resolver import TargetResolver
from app.agent.planning.action_plan import ActionPlan
from app.agent.planning.action_step import ActionStep
from app.agent.runtime.execution_context import AgentExecutionContext
from app.agent.runtime.reasoning_budget import ReasoningBudget
from app.agent.runtime.resumable_task import (
    Execution,
    PlanDecision,
    ResumableTaskRunner,
    TaskAction,
    TaskCheckpoint,
    Validation,
    Verification,
    fingerprint_scene,
)
from app.agent.runtime.resumable_task_repository import TaskCheckpointRepository
from app.agent.runtime.resumable_task_service import ResumableTaskService
from app.agent.perception.windowhub_form_reader import WindowHubFormReader


_ALLOWED_GUI_ACTIONS = frozenset({"click_screen_element", "write_text"})
_VALUE_PATTERN = re.compile(r"^\s*([+-]?\d+(?:[.,]\d+)?)\s*(?:mm|cm|m)?\s*$", re.IGNORECASE)


class WindowHubResumableTaskHost:
    """Connect a WindowHub control loop and orchestrator to persisted task cycles.

    A host is intentionally constructed with explicit dependencies. It doesn't
    enable live mode itself and never creates a control loop that picks an
    arbitrary foreground window. The supplied control loop retains ownership of
    action preparation, decision policy, execution and its normal verification.
    """

    def __init__(
        self,
        *,
        control_loop,
        orchestrator,
        repository: TaskCheckpointRepository | None = None,
        final_verifier: Callable[[TaskCheckpoint, object], Verification] | None = None,
    ) -> None:
        if (
            control_loop is None
            or not callable(getattr(control_loop, "observe_scene", None))
            or not callable(getattr(control_loop, "run", None))
        ):
            raise ValueError(
                "A WindowHub control loop with observe_scene() and run() is required."
            )
        if orchestrator is None or not callable(getattr(orchestrator, "prepare", None)):
            raise ValueError("An agent orchestrator with prepare() is required.")
        self.control_loop = control_loop
        self.orchestrator = orchestrator
        self.repository = repository or TaskCheckpointRepository()
        self.final_verifier = final_verifier or verify_windowhub_final_state
        self.service = ResumableTaskService(
            repository=self.repository,
            runner_factory=self._build_runner,
        )

    def _build_runner(self, checkpoint: TaskCheckpoint) -> ResumableTaskRunner:
        return ResumableTaskRunner(
            observe=self.control_loop.observe_scene,
            plan_next=self._plan_next,
            validate_action=self._validate_target,
            execute_action=self._execute_one,
            verify_action=self._verify_action,
            verify_final_state=self.final_verifier,
        )

    def _plan_next(self, checkpoint: TaskCheckpoint, scene: object) -> PlanDecision:
        remaining = checkpoint.max_reasoning_calls - checkpoint.reasoning_calls
        if remaining < 1:
            return PlanDecision(unresolved_issues=("Reasoning budget exhausted.",))

        request_message = self._render_task_prompt(checkpoint)
        request = AgentRequest(
            message=request_message,
            session_id=checkpoint.task_id,
            metadata={
                "target_application": "WindowHub",
                "resumable_task_id": checkpoint.task_id,
            },
        )
        budget = ReasoningBudget(max_calls=remaining)
        try:
            context = self.orchestrator.prepare(
                request,
                initial_scene=scene,
                application_knowledge=get_windowhub_offer_knowledge(),
                autonomous=True,
                reasoning_budget=budget,
            )
        except TypeError as exc:
            # Keep old/custom orchestrators usable only when they explicitly
            # identify which optional parameter they don't implement.
            if "unexpected keyword argument" not in str(exc) or not any(
                key in str(exc) for key in ("application_knowledge", "autonomous", "reasoning_budget")
            ):
                raise
            context = self.orchestrator.prepare(
                request,
                initial_scene=scene,
            )

        plan = getattr(context, "plan", None)
        if bool(getattr(context, "requires_manual_review", False)):
            reason = None
            getter = getattr(context, "get_value", None)
            if callable(getter):
                reason = getter("task_reasoning_failure")
            return PlanDecision(
                unresolved_issues=(
                    f"Agent planner requires review: {reason or 'manual_review'}",
                )
            )

        if plan is None:
            return PlanDecision(
                unresolved_issues=("Agent planner produced no action plan.",)
            )

        if bool(getattr(plan, "completed", False)):
            return PlanDecision(complete=True)

        steps = tuple(getattr(plan, "steps", ()) or ())
        if not steps:
            return PlanDecision(
                unresolved_issues=("Agent planner produced no next GUI action.",)
            )

        proposed = steps[0].action
        if proposed.name not in _ALLOWED_GUI_ACTIONS:
            return PlanDecision(
                unresolved_issues=(
                    f"Unsupported WindowHub GUI action: {proposed.name}",
                )
            )

        if not isinstance(proposed.target, str) or not proposed.target.strip():
            return PlanDecision(
                unresolved_issues=("Agent planner proposed an action without a semantic target.",)
            )

        if proposed.name == "write_text" and not isinstance(proposed.value, str):
            return PlanDecision(
                unresolved_issues=("Agent planner proposed write_text without a value.",)
            )

        matched_field = _field_for_target(proposed.target)
        if proposed.name == "write_text" and matched_field in checkpoint.required_fields:
            if matched_field not in checkpoint.facts:
                return PlanDecision(
                    required_fields=(matched_field,),
                )
            expected = checkpoint.facts[matched_field]
            if not _values_match(expected, proposed.value):
                return PlanDecision(
                    unresolved_issues=(
                        f"Proposed value for {matched_field!r} conflicts with the task's supplied fact; no text was entered.",
                    )
                )

        intent = getattr(getattr(context, "intent", None), "value", None)
        if not isinstance(intent, str):
            intent = getattr(getattr(plan, "intent", None), "value", "computer_use")
        description = proposed.description if isinstance(proposed.description, str) else proposed.name

        task_action = TaskAction(
            action_id=f"{checkpoint.task_id}:{checkpoint.actions_used + 1}:{proposed.name}:{proposed.target}",
            name=proposed.name,
            target=proposed.target.strip(),
            scene_fingerprint=fingerprint_scene(scene),
            value=proposed.value,
            expected_state={
                "intent": intent,
                "description": description,
                "request_message": request_message,
                "source_plan_confidence": getattr(plan, "confidence", 0.0),
                "task_id": checkpoint.task_id,
            },
            requires_confirmation=bool(proposed.requires_confirmation),
        )
        return PlanDecision(action=task_action)

    @staticmethod
    def _render_task_prompt(checkpoint: TaskCheckpoint) -> str:
        facts = json.dumps(
            checkpoint.facts,
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        )
        verified = [
            {
                "action": step.action_name,
                "target": step.actual_target or step.requested_target,
                "evidence": list(step.evidence),
            }
            for step in checkpoint.completed_steps
        ]
        progress = json.dumps(verified, ensure_ascii=False, sort_keys=True, default=str)
        return (
            f"WindowHub task goal: {checkpoint.goal}\n"
            f"Supplied task facts (do not change these values): {facts}\n"
            f"Previously completed and verified steps: {progress}\n"
            f"Current task status: {checkpoint.status.value}\n"
            "Plan only the next single semantic GUI action from the current visible scene. "
            "Do not repeat completed steps, infer missing commercial choices, or use coordinates. "
            "Prepare a draft only; never send or submit without an explicit approval checkpoint."
        )

    @staticmethod
    def _validate_target(action: TaskAction, scene: object) -> Validation:
        try:
            resolution = TargetResolver().resolve(scene, action.target)
        except (AttributeError, TypeError, ValueError) as exc:
            return Validation(False, reason=f"semantic_target_resolution_failed:{type(exc).__name__}")
        if not resolution.resolved or resolution.element is None:
            return Validation(False, reason=resolution.reason or "semantic target unresolved")
        if action.name == "write_text":
            metadata = getattr(resolution.element, "metadata", None) or {}
            if not isinstance(metadata, Mapping):
                metadata = {}

            kind = str(getattr(resolution.element, "kind", "") or "").strip().casefold()
            capability = getattr(getattr(resolution.element, "interaction_capability", None), "value",
                                 getattr(resolution.element, "interaction_capability", None))
            capability = str(capability or "").strip().casefold()
            editable_kind = kind in {"edit", "textbox", "text_box", "combobox"}
            editable_capability = capability in {
                "writable", "editable", "text_entry", "textentry",
            }
            if not (editable_kind or editable_capability):
                return Validation(
                    False,
                    reason="write_text target is not an evidenced editable text field",
                )

            # WindowHub needs a stricter write policy than the shared generic
            # resolver: unique-but-unscoped controls are not enough evidence
            # to type into a commercial document field.
            active_document = getattr(scene, "active_document", None)
            if isinstance(active_document, str) and active_document.strip():
                document_scope = metadata.get("document_scope")
                is_active_document_field = (
                    isinstance(document_scope, str)
                    and document_scope.strip() == active_document.strip()
                )
                is_owned_modal_field = metadata.get("uia_owned_modal") is True
                if not (is_active_document_field or is_owned_modal_field):
                    return Validation(
                        False,
                        reason=(
                            "write_text target lacks active-document or "
                            "explicit owned-modal scope evidence"
                        ),
                    )
            elif not metadata.get("uia_owned_modal") is True:
                return Validation(
                    False,
                    reason=(
                        "write_text target requires a resolved active document "
                        "or explicit owned-modal scope evidence"
                    ),
                )
        return Validation(
            True,
            target=resolution.element.label,
            reason=resolution.reason,
            element=resolution.element,
        )

    def _execute_one(
        self,
        action: TaskAction,
        scene: object,
        validation: Validation,
    ) -> Execution:
        intent_value = action.expected_state.get("intent", AgentIntent.COMPUTER_USE.value)
        try:
            intent = AgentIntent(str(intent_value))
        except ValueError:
            intent = AgentIntent.COMPUTER_USE

        description = action.expected_state.get("description")
        if not isinstance(description, str) or not description.strip():
            description = f"Continue WindowHub task toward: {action.target}"

        agent_action = AgentAction(
            name=action.name,
            description=description,
            # ResumableTaskRunner has already enforced the confirmation gate
            # for this exact TaskAction before calling the executor callback.
            requires_confirmation=False,
            target=validation.target or action.target,
            value=action.value,
            requires_environment_observation=True,
        )
        request_message = action.expected_state.get("request_message")
        request = AgentRequest(
            message=request_message if isinstance(request_message, str) else description,
            session_id=str(action.expected_state.get("task_id") or action.action_id),
            metadata={"target_application": "WindowHub", "resumable_task_action_id": action.action_id},
        )
        plan = ActionPlan(
            intent=intent,
            steps=(ActionStep(index=1, action=agent_action),),
            confidence=1.0,
            requires_manual_review=False,
            completed=False,
        )
        context = AgentExecutionContext(
            request=request,
            intent=intent,
            plan=plan,
            capability=None,
            skill=None,
            requires_manual_review=False,
        )
        context.update_scene(scene)

        # The runner calls this method only after current-scene target
        # validation and (when needed) action-bound confirmation. Transfer
        # that approval to the existing DecisionEngine for this exact action.
        from app.agent.runtime.confirmation import action_confirmation_key
        context.set_value("confirmed_action_key", action_confirmation_key(agent_action))

        try:
            control_result = self.control_loop.run(plan=plan, context=context)
        except Exception as exc:
            # Once control has been handed to the GUI layer, conservatively
            # record that execution might have occurred; never auto-replay.
            return Execution(
                success=False,
                executed=True,
                message=f"control_loop_raised:{type(exc).__name__}",
                actual_target=validation.target or action.target,
                executor_path="windowhub_control_loop",
                metadata={"control_loop_exception": type(exc).__name__},
            )

        execution_loop = getattr(control_result, "last_execution_result", None)
        attempt = getattr(execution_loop, "last_attempt", None)
        raw_result = getattr(attempt, "execution_result", None)
        metadata = getattr(raw_result, "metadata", None) or {}
        if not isinstance(metadata, Mapping):
            metadata = {}

        executed_count = getattr(control_result, "executed_actions", 0)
        executed = metadata.get("executed") is not False and bool(executed_count)
        raw_success = getattr(raw_result, "success", None)
        success = (
            bool(getattr(control_result, "success", False))
            and not bool(getattr(control_result, "requires_manual_review", False))
            and not bool(getattr(control_result, "stopped", False))
            and (raw_success is None or bool(raw_success))
        )
        verification_result = getattr(attempt, "verification_result", None)
        inner_verified = bool(getattr(verification_result, "verified", False))

        return Execution(
            success=success,
            executed=executed,
            message=str(getattr(raw_result, "message", "control_loop_action_finished")),
            actual_target=str(metadata.get("target") or validation.target or action.target),
            executor_path=str(metadata.get("execution_path") or "windowhub_control_loop"),
            metadata={
                "control_loop_verified": inner_verified,
                "control_loop_success": bool(getattr(control_result, "success", False)),
                "requires_manual_review": bool(getattr(control_result, "requires_manual_review", False)),
                "plan_status": str(getattr(getattr(control_result, "plan_status", None), "value",
                                           getattr(control_result, "plan_status", ""))),
            },
        )

    @staticmethod
    def _verify_action(
        action: TaskAction,
        execution: Execution,
        post_scene: object,
    ) -> Verification:
        if not execution.executed or not execution.success:
            return Verification(False, reason=execution.message or "control loop did not complete successfully")

        if action.name == "write_text":
            candidates = [
                element for element in getattr(post_scene, "elements", ())
                if isinstance(getattr(element, "label", None), str)
                and element.label.strip().casefold() == action.target.strip().casefold()
            ]
            matching = [
                element for element in candidates
                if isinstance((getattr(element, "metadata", {}) or {}).get("current_value"), str)
                and _values_match(action.value, (getattr(element, "metadata", {}) or {}).get("current_value"))
            ]
            if len(candidates) != 1 or len(matching) != 1:
                return Verification(
                    False,
                    evidence=tuple({"label": getattr(e, "label", None),
                                    "current_value": (getattr(e, "metadata", {}) or {}).get("current_value")}
                                   for e in candidates),
                    reason="Written value was not independently observed in the target field.",
                )
            return Verification(
                True,
                evidence=({"field": action.target,
                           "observed_value": (matching[0].metadata or {}).get("current_value"),
                           "source": "fresh_windowhub_scene"},),
            )

        changed = fingerprint_scene(post_scene) != action.scene_fingerprint
        inner_verified = execution.metadata.get("control_loop_verified") is True
        if not (changed or inner_verified):
            return Verification(
                False,
                evidence=({"target": action.target,
                           "post_scene_fingerprint": fingerprint_scene(post_scene)},),
                reason="Click succeeded but no independently verified state transition was observed.",
            )
        return Verification(
            True,
            evidence=({"target": action.target,
                       "post_scene_fingerprint": fingerprint_scene(post_scene),
                       "scene_changed": changed,
                       "control_loop_verified": inner_verified},),
        )


def verify_windowhub_final_state(
    checkpoint: TaskCheckpoint,
    scene: object,
) -> Verification:
    """Compare required task facts against uniquely observed WindowHub fields."""
    if not checkpoint.required_fields:
        return Verification(
            False,
            evidence=({"reason": "no_required_fields_configured"},),
            reason="Final-state verification needs explicit required fields.",
        )

    active_document = getattr(scene, "active_document", None)
    if not isinstance(active_document, str) or not active_document.strip():
        return Verification(
            False,
            evidence=({"reason": "active_document_unresolved"},),
            missing_fields=tuple(checkpoint.required_fields),
            reason=(
                "Active document is unresolved; refusing cross-document "
                "final-state verification."
            ),
        )

    try:
        reader = WindowHubFormReader()
        # Final-state verification must only consume fields proven to belong
        # to the uniquely resolved active document. Falling back to read()
        # would allow a matching value from another document or a generic
        # dialog/viewer to satisfy the quote's required fields.
        form_fields = reader.read_active_document(scene)
    except (AttributeError, TypeError, ValueError) as exc:
        return Verification(False, reason=f"windowhub_form_read_failed:{type(exc).__name__}")

    evidence: list[dict[str, object]] = []
    missing: list[str] = []
    conflicts: list[str] = []
    for field_name in checkpoint.required_fields:
        if field_name not in checkpoint.facts:
            missing.append(field_name)
            continue
        aliases = _aliases_for_field(field_name)
        candidates = [
            item for item in form_fields
            if _canonical(item.label) in aliases
            or any(alias and alias in _canonical(item.label) for alias in aliases if len(alias) >= 4)
        ]
        if len(candidates) != 1:
            missing.append(field_name)
            evidence.append({
                "field": field_name,
                "candidate_count": len(candidates),
                "status": "missing_or_ambiguous",
            })
            continue
        item = candidates[0]
        value = item.value
        evidence.append({
            "field": field_name,
            "label": item.label,
            "observed_value": value,
            "expected_value": checkpoint.facts[field_name],
            "scope_status": item.scope_status,
        })
        if value is None or not _values_match(checkpoint.facts[field_name], value):
            conflicts.append(field_name)

    if missing or conflicts:
        reasons = []
        if missing:
            reasons.append("missing or ambiguous fields: " + ", ".join(missing))
        if conflicts:
            reasons.append("observed values do not match supplied facts: " + ", ".join(conflicts))
        return Verification(
            False,
            evidence=tuple(evidence),
            missing_fields=tuple(dict.fromkeys((*missing, *conflicts))),
            reason="; ".join(reasons),
        )
    return Verification(
        True,
        evidence=tuple(evidence),
        reason="Every required field was uniquely observed and matched its supplied fact.",
    )


def _field_for_target(target: str) -> str | None:
    normalized = _canonical(target)
    for field_name in get_windowhub_offer_knowledge().get("field_synonyms", {}):
        aliases = _aliases_for_field(field_name)
        if normalized in aliases or any(alias and alias in normalized for alias in aliases if len(alias) >= 4):
            return field_name
    return None


def _aliases_for_field(field_name: str) -> set[str]:
    synonyms = get_windowhub_offer_knowledge().get("field_synonyms", {})
    values = synonyms.get(field_name, ()) if isinstance(synonyms, Mapping) else ()
    return {_canonical(field_name), *(_canonical(v) for v in values if isinstance(v, str) and v.strip())}


def _canonical(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.strip().casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _values_match(expected: object, actual: object) -> bool:
    if expected is None or actual is None:
        return False
    if isinstance(expected, (int, float, Decimal)) and not isinstance(expected, bool):
        expected_text = str(expected)
        actual_text = str(actual)
        left = _numeric_value(expected_text)
        right = _numeric_value(actual_text)
        return left is not None and right is not None and left == right
    if isinstance(actual, (int, float, Decimal)) and not isinstance(actual, bool):
        return _values_match(str(actual), expected)
    left = _numeric_value(str(expected))
    right = _numeric_value(str(actual))
    if left is not None and right is not None:
        return left == right
    return str(expected).strip().casefold() == str(actual).strip().casefold()


def _numeric_value(value: str) -> Decimal | None:
    match = _VALUE_PATTERN.match(value)
    if not match:
        return None
    try:
        return Decimal(match.group(1).replace(",", "."))
    except InvalidOperation:
        return None
