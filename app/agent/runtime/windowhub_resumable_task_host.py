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
from app.agent.perception.windowhub_grid_reader import WindowHubGridReader


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
        multi_windows = checkpoint.facts.get("windows")
        if (
            proposed.name == "write_text"
            and isinstance(multi_windows, (list, tuple))
            and matched_field in {"width", "height", "quantity"}
        ):
            position_number = _position_number_from_target_or_scene(
                proposed.target,
                scene,
            )
            if position_number is None:
                return PlanDecision(
                    unresolved_issues=(
                        "Multi-window entry requires one unambiguous visible position "
                        "number before typing width, height, or quantity. No value was entered.",
                    )
                )
            matching_positions = [
                item for item in multi_windows
                if isinstance(item, Mapping)
                and item.get("position_number") == position_number
            ]
            if len(matching_positions) != 1:
                return PlanDecision(
                    unresolved_issues=(
                        f"Position {position_number} is not uniquely present in the reviewed task rows. No value was entered.",
                    )
                )
            reviewed_position = matching_positions[0]
            if reviewed_position.get("human_confirmed") is not True:
                return PlanDecision(
                    unresolved_issues=(
                        f"Position {position_number} does not have explicit human confirmation. No value was entered.",
                    )
                )
            expected_field = {
                "width": "width_mm",
                "height": "height_mm",
                "quantity": "quantity",
            }[matched_field]
            expected_value = reviewed_position.get(expected_field)
            if expected_value is None:
                return PlanDecision(
                    required_fields=(
                        f"windows[{position_number}].{expected_field}",
                    ),
                )
            if not _values_match_for_field(matched_field, expected_value, proposed.value):
                return PlanDecision(
                    unresolved_issues=(
                        f"Proposed {matched_field} for position {position_number} conflicts with its human-reviewed value. No text was entered.",
                    )
                )
        if proposed.name == "write_text" and matched_field in checkpoint.required_fields:
            if matched_field not in checkpoint.facts:
                return PlanDecision(
                    required_fields=(matched_field,),
                )
            expected = checkpoint.facts[matched_field]
            if not _values_match_for_field(matched_field, expected, proposed.value):
                return PlanDecision(
                    unresolved_issues=(
                        f"Proposed value for {matched_field!r} conflicts with the task's supplied fact; no text was entered.",
                    )
                )
        if proposed.name == "click_screen_element" and matched_field == "product_type":
            expected_code = _product_type_code(checkpoint.facts.get("product_type"))
            selected_code = _product_type_code(proposed.target)
            if (
                expected_code is not None
                and selected_code is not None
                and selected_code != expected_code
            ):
                return PlanDecision(
                    unresolved_issues=(
                        f"Proposed product selection {proposed.target!r} conflicts with "
                        f"the task's supplied product_type; no selection was made.",
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
        multi_window_rules = ""
        if isinstance(checkpoint.facts.get("windows"), (list, tuple)):
            multi_window_rules = (
                " MULTI-POSITION RULES: Preserve each reviewed windows[] entry as a separate "
                "offer line in the supplied order. Never merge, drop, duplicate or reorder positions. "
                "Before typing a width, height or quantity, the current visible scene or exact "
                "semantic target must identify one unique Position number; otherwise request manual "
                "review without typing. Every numeric value must match the reviewed facts for that "
                "specific position. Verify each mutation against a fresh scene. Unknown profile, "
                "glazing, opening, colour and price must not be invented. Saving the draft is the "
                "maximum permitted goal; never send, submit, publish, approve or finalize it, even "
                "if a submission button is visible."
            )
        return (
            f"WindowHub task goal: {checkpoint.goal}\n"
            f"Supplied task facts (do not change these values): {facts}\n"
            f"Previously completed and verified steps: {progress}\n"
            f"Current task status: {checkpoint.status.value}\n"
            "Plan only the next single semantic GUI action from the current visible scene. "
            "Do not repeat completed steps, infer missing commercial choices, or use coordinates. "
            "Prepare a draft only; never send or submit without an explicit approval checkpoint."
            f"{multi_window_rules}"
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
            raw_document_scope = metadata.get("document_scope")
            document_scope = (
                raw_document_scope.strip()
                if isinstance(raw_document_scope, str) and raw_document_scope.strip()
                else None
            )
            is_owned_modal_field = metadata.get("uia_owned_modal") is True

            if isinstance(active_document, str) and active_document.strip():
                active_document_scope = active_document.strip()
                is_active_document_field = document_scope == active_document_scope

                # Explicit modal ownership is evidence for an otherwise
                # unscoped dialog field; it must not override contradictory
                # evidence that the target belongs to a different offer.
                if document_scope is not None and not is_active_document_field:
                    return Validation(
                        False,
                        reason="write_text target is scoped to a different document",
                    )
                if not (is_active_document_field or is_owned_modal_field):
                    return Validation(
                        False,
                        reason=(
                            "write_text target lacks active-document or "
                            "explicit owned-modal scope evidence"
                        ),
                    )
            elif not is_owned_modal_field:
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

    if "windows" in checkpoint.facts or "windows" in checkpoint.required_fields:
        return _verify_windowhub_multi_window_state(
            checkpoint,
            scene,
            active_document=active_document,
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
        if field_name == "product_type":
            status, product_evidence = _verify_product_type(
                expected=checkpoint.facts[field_name],
                scene=scene,
                form_fields=form_fields,
                active_document=active_document,
            )
            evidence.append(product_evidence)
            if status == "missing":
                missing.append(field_name)
            elif status != "matched":
                conflicts.append(field_name)
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


_POSITION_HEADER_PATTERN = re.compile(
    r"^\s*(?:position|pozycja|pos\.?)\s*#?\s*(\d+)\s*$",
    re.IGNORECASE,
)
_POSITION_ANY_PATTERN = re.compile(
    r"\b(?:position|pozycja|pos\.?)\s*#?\s*(\d+)\b",
    re.IGNORECASE,
)
_GRID_DIMENSIONS_PATTERN = re.compile(
    r"^\s*(\d{3,4})(?:\s*mm)?\s*[x×*]\s*(\d{3,4})(?:\s*mm)?\s*$",
    re.IGNORECASE,
)
_GRID_SCALAR_DIMENSION_PATTERN = re.compile(
    r"^\s*(\d{3,4})(?:\s*mm)?\s*$",
    re.IGNORECASE,
)
_GRID_QUANTITY_PATTERN = re.compile(
    r"^\s*(?:(?:menge|quantity|qty|anzahl|il[oó]s[cć])\s*[:=]?\s*)?"
    r"(\d{1,3})(?:\s*(?:szt\.?|sztuk|sztuki|pcs?|pieces?))?\s*$",
    re.IGNORECASE,
)
_WINDOW_PRODUCT_PATTERN = re.compile(
    r"\b(?:okno|okna|okien|window|windows)\b",
    re.IGNORECASE,
)


def _position_number_from_target_or_scene(target: str, scene: object) -> int | None:
    """Resolve one explicit row number; never infer it from row order."""
    target_match = _POSITION_ANY_PATTERN.search(target)
    if target_match is not None:
        try:
            return int(target_match.group(1))
        except (TypeError, ValueError):
            return None

    active_document = getattr(scene, "active_document", None)
    if not isinstance(active_document, str) or not active_document.strip():
        return None

    matches: list[int] = []
    for element in getattr(scene, "elements", ()) or ():
        metadata = getattr(element, "metadata", None) or {}
        if not isinstance(metadata, Mapping):
            continue
        scope = metadata.get("document_scope")
        if not isinstance(scope, str) or scope.strip() != active_document.strip():
            continue
        label = getattr(element, "label", None)
        if not isinstance(label, str):
            continue
        matched = _POSITION_HEADER_PATTERN.fullmatch(label)
        if matched is not None:
            try:
                matches.append(int(matched.group(1)))
            except (TypeError, ValueError):
                continue
    # Duplicated or multiple position headers are ambiguous, even if their
    # numbers appear sequential. The caller must resolve the active position.
    return matches[0] if len(matches) == 1 else None


def _grid_cell_texts(cell: object) -> tuple[str, ...]:
    values: list[str] = []
    label = getattr(cell, "label", None)
    if isinstance(label, str) and label.strip():
        values.append(label.strip())
    if getattr(cell, "value_available", False) is True:
        value = getattr(cell, "value", None)
        if isinstance(value, str) and value.strip():
            values.append(value.strip())
    return tuple(dict.fromkeys(values))


def _grid_cell_dimension_pairs(cell: object) -> set[tuple[int, int]]:
    pairs: set[tuple[int, int]] = set()
    for value in _grid_cell_texts(cell):
        match = _GRID_DIMENSIONS_PATTERN.fullmatch(value)
        if match is not None:
            pairs.add((int(match.group(1)), int(match.group(2))))
    return pairs


def _grid_cell_scalar_dimensions(cell: object) -> set[int]:
    dimensions: set[int] = set()
    for value in _grid_cell_texts(cell):
        match = _GRID_SCALAR_DIMENSION_PATTERN.fullmatch(value)
        if match is not None:
            dimensions.add(int(match.group(1)))
    return dimensions


def _grid_cell_quantities(cell: object) -> set[int]:
    quantities: set[int] = set()
    for value in _grid_cell_texts(cell):
        match = _GRID_QUANTITY_PATTERN.fullmatch(value)
        if match is not None:
            quantities.add(int(match.group(1)))
    return quantities


def _grid_row_describes_window(row: tuple[object | None, ...]) -> bool:
    return any(
        _WINDOW_PRODUCT_PATTERN.search(value) is not None
        for cell in row
        if cell is not None
        for value in _grid_cell_texts(cell)
    )


def _verify_windowhub_multi_window_state(
    checkpoint: TaskCheckpoint,
    scene: object,
    *,
    active_document: str,
) -> Verification:
    """Require a unique, complete active-document grid matching every reviewed row."""
    required = tuple(checkpoint.required_fields)
    windows = checkpoint.facts.get("windows")
    if not isinstance(windows, (list, tuple)) or not windows:
        return Verification(
            False,
            evidence=({"reason": "reviewed_windows_fact_missing"},),
            missing_fields=required or ("windows",),
            reason="Multi-window final verification requires the reviewed windows list.",
        )
    if _product_type_code(checkpoint.facts.get("product_type")) != "window":
        return Verification(
            False,
            evidence=({"reason": "unsupported_multi_window_product_type"},),
            missing_fields=("product_type",),
            reason="This multi-row verifier accepts window offers only.",
        )

    expected_signatures: list[tuple[int, int, int]] = []
    position_numbers: list[int] = []
    for item in windows:
        if not isinstance(item, Mapping) or item.get("human_confirmed") is not True:
            return Verification(
                False,
                evidence=({"reason": "unreviewed_or_malformed_window_row"},),
                missing_fields=("windows",),
                reason="Every expected offer row must have explicit human confirmation.",
            )
        position_number = item.get("position_number")
        width = item.get("width_mm")
        height = item.get("height_mm")
        quantity = item.get("quantity")
        if (
            any(not isinstance(value, int) or isinstance(value, bool) for value in
                (position_number, width, height, quantity))
            or position_number < 1
            or not 200 <= width <= 6000
            or not 200 <= height <= 6000
            or not 1 <= quantity <= 1000
        ):
            return Verification(
                False,
                evidence=({"reason": "invalid_reviewed_window_row"},),
                missing_fields=("windows",),
                reason="Reviewed window rows have invalid dimensions or quantity.",
            )
        position_numbers.append(position_number)
        expected_signatures.append((width, height, quantity))

    if len(set(position_numbers)) != len(position_numbers):
        return Verification(
            False,
            evidence=({"reason": "duplicate_position_number"},),
            missing_fields=("windows",),
            reason="Reviewed window position numbers are not unique.",
        )
    if position_numbers != sorted(position_numbers):
        return Verification(
            False,
            evidence=({"reason": "position_order_changed"},),
            missing_fields=("windows",),
            reason="Reviewed window rows must remain in their supplied position order.",
        )
    if (
        checkpoint.facts.get("position_count") != len(windows)
        or checkpoint.facts.get("total_quantity")
        != sum(signature[2] for signature in expected_signatures)
    ):
        return Verification(
            False,
            evidence=({"reason": "reviewed_position_count_or_quantity_inconsistent"},),
            missing_fields=("position_count", "total_quantity"),
            reason="The checkpoint's position count or total quantity conflicts with its reviewed rows.",
        )

    try:
        grids = WindowHubGridReader().read_active_document(scene)
    except (AttributeError, TypeError, ValueError) as exc:
        return Verification(
            False,
            evidence=({"reason": f"windowhub_grid_read_failed:{type(exc).__name__}"},),
            missing_fields=required or ("windows",),
            reason="Could not read active-document grid evidence safely.",
        )

    successful_layouts: list[tuple[object, str, tuple[int, ...], list[tuple[int, int, int]]]] = []
    for grid in grids:
        if (
            grid.scope_status != "active_document"
            or grid.complete is not True
            or grid.row_count != len(windows)
            or len(grid.rows) != len(windows)
            or grid.column_count < 2
        ):
            continue
        rows = grid.rows
        if any(
            any(cell is None for cell in row)
            or not _grid_row_describes_window(row)
            for row in rows
        ):
            continue

        # Try only complete, stable column mappings. Ambiguous text/value
        # evidence in any selected cell invalidates that mapping.
        for dimension_column in range(grid.column_count):
            for quantity_column in range(grid.column_count):
                if dimension_column == quantity_column:
                    continue
                observed: list[tuple[int, int, int]] = []
                valid = True
                for row in rows:
                    dim_pairs = _grid_cell_dimension_pairs(row[dimension_column])
                    quantities = _grid_cell_quantities(row[quantity_column])
                    if len(dim_pairs) != 1 or len(quantities) != 1:
                        valid = False
                        break
                    width, height = next(iter(dim_pairs))
                    quantity = next(iter(quantities))
                    observed.append((width, height, quantity))
                if valid and observed == expected_signatures:
                    successful_layouts.append(
                        (grid, "combined_dimensions", (dimension_column, quantity_column), observed)
                    )

        for width_column in range(grid.column_count):
            for height_column in range(grid.column_count):
                for quantity_column in range(grid.column_count):
                    if len({width_column, height_column, quantity_column}) != 3:
                        continue
                    observed = []
                    valid = True
                    for row in rows:
                        widths = _grid_cell_scalar_dimensions(row[width_column])
                        heights = _grid_cell_scalar_dimensions(row[height_column])
                        quantities = _grid_cell_quantities(row[quantity_column])
                        if len(widths) != 1 or len(heights) != 1 or len(quantities) != 1:
                            valid = False
                            break
                        observed.append((
                            next(iter(widths)),
                            next(iter(heights)),
                            next(iter(quantities)),
                        ))
                    if valid and sorted(observed) == sorted(expected_signatures):
                        successful_layouts.append(
                            (
                                grid,
                                "separate_dimensions",
                                (width_column, height_column, quantity_column),
                                observed,
                            )
                        )

    if len(successful_layouts) != 1:
        reason = (
            "No complete active-document grid uniquely matches every reviewed window row."
            if not successful_layouts
            else "More than one grid layout matches; final verification is ambiguous."
        )
        return Verification(
            False,
            evidence=({
                "active_document": active_document,
                "active_grid_count": len(grids),
                "matching_layout_count": len(successful_layouts),
                "expected_position_count": len(windows),
                "expected_total_quantity": sum(signature[2] for signature in expected_signatures),
            },),
            missing_fields=required or ("windows",),
            reason=reason,
        )

    grid, layout, columns, observed_signatures = successful_layouts[0]
    evidence: list[dict[str, object]] = []
    for row_index, item in enumerate(windows):
        signature = observed_signatures[row_index]
        expected_signature = (
            item["width_mm"],
            item["height_mm"],
            item["quantity"],
        )
        if signature != expected_signature:
            return Verification(
                False,
                evidence=tuple(evidence),
                missing_fields=("windows",),
                reason="A reviewed position does not match its corresponding grid row.",
            )
        evidence.append({
            "field": f"windows[{item['position_number']}]",
            "grid_row_index": row_index,
            "position_number": item["position_number"],
            "expected_width_mm": item["width_mm"],
            "observed_width_mm": signature[0],
            "expected_height_mm": item["height_mm"],
            "observed_height_mm": signature[1],
            "expected_quantity": item["quantity"],
            "observed_quantity": signature[2],
            "human_confirmed": True,
            "grid_layout": layout,
            "verification": "complete_active_document_grid_row",
        })

    evidence.extend((
        {"field": "position_count", "expected_value": len(windows), "observed_value": len(observed_signatures)},
        {
            "field": "total_quantity",
            "expected_value": sum(signature[2] for signature in expected_signatures),
            "observed_value": sum(signature[2] for signature in observed_signatures),
        },
    ))
    return Verification(
        True,
        evidence=tuple(evidence),
        reason="Every reviewed window row independently matches the complete active-document grid.",
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


def _product_type_code(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = _canonical(value)
    aliases = {
        "window": "window",
        "windows": "window",
        "okno": "window",
        "okna": "window",
        "door": "door",
        "drzwi": "door",
        "balcony door": "balcony_door",
        "drzwi balkonowe": "balcony_door",
        "sliding door": "sliding_door",
        "drzwi przesuwne": "sliding_door",
        "przesuwne": "sliding_door",
        "hs": "sliding_door",
        "h.s.": "sliding_door",
    }
    return aliases.get(normalized)


def _values_match_for_field(
    field_name: str | None,
    expected: object,
    actual: object,
) -> bool:
    if field_name == "product_type":
        left = _product_type_code(expected)
        right = _product_type_code(actual)
        return left is not None and right is not None and left == right
    return _values_match(expected, actual)


def _verify_product_type(
    *,
    expected: object,
    scene: object,
    form_fields: tuple[object, ...],
    active_document: str,
) -> tuple[str, dict[str, object]]:
    expected_code = _product_type_code(expected)
    if expected_code is None:
        return "conflict", {
            "field": "product_type",
            "expected_value": expected,
            "status": "unsupported_expected_product_type",
        }

    field_label_aliases = {
        "rodzaj produktu",
        "typ produktu",
        "produkt",
        "product type",
    }
    labelled_fields = [
        item
        for item in form_fields
        if _canonical(getattr(item, "label", "")) in field_label_aliases
        and _product_type_code(getattr(item, "value", None)) is not None
    ]
    if len(labelled_fields) == 1:
        item = labelled_fields[0]
        observed = getattr(item, "value", None)
        observed_code = _product_type_code(observed)
        evidence = {
            "field": "product_type",
            "label": getattr(item, "label", None),
            "observed_value": observed,
            "expected_value": expected,
            "scope_status": getattr(item, "scope_status", None),
            "verification": "active_document_product_field",
        }
        return ("matched" if observed_code == expected_code else "conflict", evidence)
    if len(labelled_fields) > 1:
        return "missing", {
            "field": "product_type",
            "candidate_count": len(labelled_fields),
            "status": "ambiguous_product_fields",
        }

    selected_items: list[tuple[object, str]] = []
    for element in getattr(scene, "elements", ()) or ():
        metadata = getattr(element, "metadata", None) or {}
        if not isinstance(metadata, Mapping):
            continue
        if metadata.get("document_scope") != active_document:
            continue
        is_selected = any(
            metadata.get(key) is True
            for key in ("uia_selected", "selected", "checked")
        )
        if not is_selected:
            continue
        code = _product_type_code(getattr(element, "label", None))
        if code is not None:
            selected_items.append((element, code))

    if len(selected_items) != 1:
        return "missing", {
            "field": "product_type",
            "candidate_count": len(selected_items),
            "status": "selected_product_missing_or_ambiguous",
        }

    element, observed_code = selected_items[0]
    evidence = {
        "field": "product_type",
        "label": getattr(element, "label", None),
        "observed_value": observed_code,
        "expected_value": expected,
        "scope_status": "active_document",
        "verification": "selected_product_item",
    }
    return ("matched" if observed_code == expected_code else "conflict", evidence)


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
