"""Durable, fail-closed one-action-at-a-time WindowHub task runner."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Callable, Mapping


class TaskStatus(str, Enum):
    READY = "ready"
    WAITING_FOR_INPUT = "waiting_for_input"
    WAITING_FOR_CONFIRMATION = "waiting_for_confirmation"
    COMPLETED = "completed"
    STOPPED = "stopped"


@dataclass(frozen=True)
class TaskAction:
    action_id: str
    name: str
    target: str
    scene_fingerprint: str
    value: str | None = None
    expected_state: Mapping[str, object] = field(default_factory=dict)
    requires_confirmation: bool = False
    submission: bool = False

    @property
    def is_submission(self) -> bool:
        text = f"{self.name} {self.target}".casefold()
        return self.submission or bool(re.search(
            r"(?<!\w)(submit|dispatch|send|publish|wyślij|wyslij|przekaż|przekaz)(?!\w)", text
        ))

    @property
    def confirmation_required(self) -> bool:
        return self.requires_confirmation or self.is_submission


@dataclass(frozen=True)
class PlanDecision:
    action: TaskAction | None = None
    complete: bool = False
    unresolved_issues: tuple[str, ...] = ()
    required_fields: tuple[str, ...] = ()

    def __post_init__(self):
        if self.action is not None and self.complete:
            raise ValueError("Planner cannot propose an action and completion together.")
        if any(not x.strip() for x in (*self.unresolved_issues, *self.required_fields)):
            raise ValueError("Planner issue/field entries must be non-empty.")


@dataclass(frozen=True)
class Validation:
    valid: bool
    target: str | None = None
    reason: str = ""
    element: object | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True)
class Execution:
    success: bool
    executed: bool
    message: str
    actual_target: str | None = None
    executor_path: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class Verification:
    verified: bool
    evidence: tuple[Mapping[str, object], ...] = ()
    missing_fields: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class StepRecord:
    cycle: int
    action_id: str
    action_name: str
    requested_target: str
    actual_target: str | None
    executor_path: str | None
    executed: bool
    execution_success: bool
    verified: bool
    evidence: tuple[Mapping[str, object], ...] = ()
    reason: str = ""

    def to_payload(self) -> dict[str, object]:
        return {"cycle": self.cycle, "action_id": self.action_id, "action_name": self.action_name,
                "requested_target": self.requested_target, "actual_target": self.actual_target,
                "executor_path": self.executor_path, "executed": self.executed,
                "execution_success": self.execution_success, "verified": self.verified,
                "evidence": _plain(self.evidence), "reason": self.reason}

    @classmethod
    def from_payload(cls, p: Mapping[str, object]) -> "StepRecord":
        return cls(int(p["cycle"]), str(p["action_id"]), str(p["action_name"]), str(p["requested_target"]),
                   _optional_str(p.get("actual_target")), _optional_str(p.get("executor_path")),
                   bool(p["executed"]), bool(p["execution_success"]), bool(p["verified"]),
                   tuple(dict(x) for x in p.get("evidence", ()) if isinstance(x, Mapping)), str(p.get("reason") or ""))


@dataclass(frozen=True)
class TaskCheckpoint:
    task_id: str
    goal: str
    facts: Mapping[str, object] = field(default_factory=dict)
    required_fields: tuple[str, ...] = ()
    unresolved_issues: tuple[str, ...] = ()
    citations: tuple[Mapping[str, object], ...] = ()
    expected_application: str | None = "WindowHub"
    status: TaskStatus = TaskStatus.READY
    max_actions: int = 12
    max_reasoning_calls: int = 12
    actions_used: int = 0
    reasoning_calls: int = 0
    steps: tuple[StepRecord, ...] = ()
    pending_action: TaskAction | None = None
    approved_action_id: str | None = None
    scene_fingerprint: str | None = None
    final_evidence: tuple[Mapping[str, object], ...] = ()
    stop_reason: str | None = None
    draft_only: bool = True
    schema_version: int = 1

    def __post_init__(self):
        if not self.task_id.strip() or not self.goal.strip(): raise ValueError("task_id and goal are required.")
        if self.schema_version != 1: raise ValueError("Unsupported checkpoint schema version.")
        if self.max_actions < 1 or self.max_reasoning_calls < 1: raise ValueError("Budgets must be positive.")
        if min(self.actions_used, self.reasoning_calls) < 0: raise ValueError("Budget counters cannot be negative.")
        if self.actions_used > self.max_actions or self.reasoning_calls > self.max_reasoning_calls:
            raise ValueError("Budget counters cannot exceed configured budgets.")

    @property
    def missing_fields(self) -> tuple[str, ...]:
        return tuple(k for k in self.required_fields if self.facts.get(k) is None or
                     (isinstance(self.facts.get(k), str) and not self.facts[k].strip()))

    @property
    def completed_steps(self) -> tuple[StepRecord, ...]:
        return tuple(s for s in self.steps if s.executed and s.execution_success and s.verified)

    def with_facts(self, values: Mapping[str, object]) -> "TaskCheckpoint":
        facts = {**self.facts, **values}
        missing_issues = {f"Missing required input: {k}" for k in values if k in self.required_fields
                          and values[k] is not None and not (isinstance(values[k], str) and not values[k].strip())}
        issues = tuple(i for i in self.unresolved_issues if i not in missing_issues)
        ready = self.status == TaskStatus.WAITING_FOR_INPUT and not issues and all(
            facts.get(k) is not None and not (isinstance(facts.get(k), str) and not facts[k].strip())
            for k in self.required_fields)
        return replace(self, facts=facts, unresolved_issues=issues,
                       status=TaskStatus.READY if ready else self.status,
                       stop_reason=None if ready else self.stop_reason)

    def resolve_issue(self, issue: str) -> "TaskCheckpoint":
        issues = tuple(i for i in self.unresolved_issues if i != issue.strip())
        ready = self.status == TaskStatus.WAITING_FOR_INPUT and not issues and not self.missing_fields
        return replace(self, unresolved_issues=issues, status=TaskStatus.READY if ready else self.status,
                       stop_reason=None if ready else self.stop_reason)

    def approve_pending_action(self, *, approve_submission: bool = False) -> "TaskCheckpoint":
        a = self.pending_action
        if self.status != TaskStatus.WAITING_FOR_CONFIRMATION or a is None:
            raise ValueError("There is no pending action awaiting confirmation.")
        if a.is_submission and not approve_submission: raise ValueError("Submission approval must be explicit.")
        return replace(self, status=TaskStatus.READY, approved_action_id=a.action_id,
                       draft_only=not a.is_submission, stop_reason=None)

    def resume_after_review(self) -> "TaskCheckpoint":
        if self.status != TaskStatus.STOPPED: raise ValueError("Only stopped checkpoints can be resumed after review.")
        return replace(self, status=TaskStatus.READY, pending_action=None, approved_action_id=None, stop_reason=None)

    def to_payload(self) -> dict[str, object]:
        a = self.pending_action
        return {"schema_version": self.schema_version, "task_id": self.task_id, "goal": self.goal,
                "facts": _plain(self.facts), "required_fields": list(self.required_fields),
                "unresolved_issues": list(self.unresolved_issues), "citations": _plain(self.citations),
                "expected_application": self.expected_application, "status": self.status.value,
                "max_actions": self.max_actions, "max_reasoning_calls": self.max_reasoning_calls,
                "actions_used": self.actions_used, "reasoning_calls": self.reasoning_calls,
                "steps": [s.to_payload() for s in self.steps],
                "pending_action": _action_payload(a) if a else None,
                "approved_action_id": self.approved_action_id, "scene_fingerprint": self.scene_fingerprint,
                "final_evidence": _plain(self.final_evidence), "stop_reason": self.stop_reason,
                "draft_only": self.draft_only}

    @classmethod
    def from_payload(cls, p: Mapping[str, object]) -> "TaskCheckpoint":
        if int(p.get("schema_version", 1)) != 1: raise ValueError("Unsupported checkpoint schema version.")
        facts, pending = p.get("facts") or {}, p.get("pending_action")
        if not isinstance(facts, Mapping): raise ValueError("facts must be an object.")
        return cls(task_id=str(p["task_id"]), goal=str(p["goal"]), facts=dict(facts),
                   required_fields=tuple(str(x) for x in p.get("required_fields", ())),
                   unresolved_issues=tuple(str(x) for x in p.get("unresolved_issues", ())),
                   citations=tuple(dict(x) for x in p.get("citations", ()) if isinstance(x, Mapping)),
                   expected_application=_optional_str(p.get("expected_application", "WindowHub")),
                   status=TaskStatus(str(p.get("status", "ready"))), max_actions=int(p.get("max_actions", 12)),
                   max_reasoning_calls=int(p.get("max_reasoning_calls", 12)), actions_used=int(p.get("actions_used", 0)),
                   reasoning_calls=int(p.get("reasoning_calls", 0)),
                   steps=tuple(StepRecord.from_payload(x) for x in p.get("steps", ()) if isinstance(x, Mapping)),
                   pending_action=_action_from_payload(pending) if isinstance(pending, Mapping) else None,
                   approved_action_id=_optional_str(p.get("approved_action_id")),
                   scene_fingerprint=_optional_str(p.get("scene_fingerprint")),
                   final_evidence=tuple(dict(x) for x in p.get("final_evidence", ()) if isinstance(x, Mapping)),
                   stop_reason=_optional_str(p.get("stop_reason")), draft_only=bool(p.get("draft_only", True)))


class ResumableTaskRunner:
    """Perform no more than one semantic action per advance call."""
    def __init__(self, *, observe: Callable[[], object], plan_next: Callable[[TaskCheckpoint, object], PlanDecision],
                 execute_action: Callable[[TaskAction, object, Validation], Execution],
                 verify_action: Callable[[TaskAction, Execution, object], Verification],
                 verify_final_state: Callable[[TaskCheckpoint, object], Verification],
                 validate_action: Callable[[TaskAction, object], Validation] | None = None):
        self.observe, self.plan_next, self.execute_action = observe, plan_next, execute_action
        self.verify_action, self.verify_final_state = verify_action, verify_final_state
        self.validate_action = validate_action or validate_semantic_target

    def advance(self, state: TaskCheckpoint) -> TaskCheckpoint:
        if state.status in (TaskStatus.COMPLETED, TaskStatus.STOPPED, TaskStatus.WAITING_FOR_CONFIRMATION): return state
        if state.missing_fields:
            issues = tuple(dict.fromkeys((*state.unresolved_issues, *(f"Missing required input: {x}" for x in state.missing_fields))))
            return replace(state, status=TaskStatus.WAITING_FOR_INPUT, unresolved_issues=issues, stop_reason="missing_required_fields")
        if state.unresolved_issues: return replace(state, status=TaskStatus.WAITING_FOR_INPUT, stop_reason="unresolved_issues")
        try: scene = self.observe()
        except Exception as exc: return self._stop(state, f"observation_failed:{type(exc).__name__}")
        fingerprint = fingerprint_scene(scene)
        if state.expected_application:
            obs = getattr(scene, "observation", None); info = getattr(obs, "state", None)
            app = f"{getattr(info, 'active_application', '') or ''} {getattr(info, 'active_window_title', '') or ''}".casefold()
            if state.expected_application.casefold() not in app:
                return self._stop(replace(state, scene_fingerprint=fingerprint), "expected_application_not_active")
        working, action = state, state.pending_action
        if action is None:
            if state.reasoning_calls >= state.max_reasoning_calls: return self._stop(replace(state, scene_fingerprint=fingerprint), "reasoning_budget_exhausted")
            try: decision = self.plan_next(state, scene)
            except Exception as exc: return self._stop(replace(state, reasoning_calls=state.reasoning_calls+1, scene_fingerprint=fingerprint), f"planning_failed:{type(exc).__name__}")
            working = replace(state, reasoning_calls=state.reasoning_calls+1, scene_fingerprint=fingerprint)
            if not isinstance(decision, PlanDecision): return self._stop(working, "invalid_planner_output")
            if decision.unresolved_issues or decision.required_fields:
                issues = tuple(dict.fromkeys((*working.unresolved_issues, *decision.unresolved_issues,
                    *(f"Missing required input: {x}" for x in decision.required_fields))))
                return replace(working, status=TaskStatus.WAITING_FOR_INPUT, unresolved_issues=issues, stop_reason="planner_needs_input")
            if decision.action is None:
                if not decision.complete: return self._stop(working, "planner_produced_no_action_and_no_completion")
                try: final = self.verify_final_state(working, scene)
                except Exception as exc: final = Verification(False, reason=f"final_verification_failed:{type(exc).__name__}")
                if final.verified:
                    return replace(working, status=TaskStatus.COMPLETED, final_evidence=final.evidence, stop_reason=None)
                reason = final.reason or "final_state_verification_failed"
                return self._stop(replace(working, final_evidence=final.evidence), reason,
                                  extra=tuple(f"Final state not verified: {x}" for x in getattr(final, "missing_fields", ())))
            action = decision.action
        elif state.scene_fingerprint != fingerprint or state.pending_action.scene_fingerprint != fingerprint:
            return self._stop(replace(state, pending_action=None, approved_action_id=None, scene_fingerprint=fingerprint), "stale_scene_before_approved_action")
        if working.actions_used >= working.max_actions: return self._stop(working, "action_budget_exhausted")
        if action.scene_fingerprint != fingerprint: return self._reject(working, action, fingerprint, "stale_scene_action_rejected_before_execution")
        try: valid = self.validate_action(action, scene)
        except Exception as exc: valid = Validation(False, reason=f"semantic_validation_failed:{type(exc).__name__}")
        if not valid.valid or not valid.target: return self._reject(working, action, fingerprint, valid.reason or "semantic_target_not_resolved", valid.target)
        if action.confirmation_required and working.approved_action_id != action.action_id:
            return replace(working, status=TaskStatus.WAITING_FOR_CONFIRMATION, pending_action=action,
                           approved_action_id=None, scene_fingerprint=fingerprint, stop_reason="confirmation_required")
        working = replace(working, actions_used=working.actions_used+1)
        try: result = self.execute_action(action, scene, valid)
        except Exception as exc: result = Execution(False, True, f"executor_raised:{type(exc).__name__}", valid.target, "unknown_after_executor_exception")
        post_scene = scene
        if result.executed:
            try:
                post_scene = self.observe()
                try: verified = self.verify_action(action, result, post_scene)
                except Exception as exc: verified = Verification(False, reason=f"action_verification_failed:{type(exc).__name__}")
            except Exception as exc: verified = Verification(False, reason=f"post_action_observation_failed:{type(exc).__name__}")
        else: verified = Verification(False, reason="action_not_executed")
        ok = result.success and result.executed and verified.verified
        why = "" if ok else (result.message or verified.reason or "action_execution_or_verification_failed")
        rec = StepRecord(len(working.steps)+1, action.action_id, action.name, action.target,
                         result.actual_target or valid.target, result.executor_path, result.executed,
                         result.success, verified.verified, verified.evidence, why)
        new = replace(working, steps=(*working.steps, rec), pending_action=None, approved_action_id=None,
                      scene_fingerprint=fingerprint_scene(post_scene), stop_reason=None)
        if not ok:
            return self._stop(new, "action_execution_failed" if not result.success else "action_verification_failed",
                              extra=(f"Step {rec.cycle} stopped safely: {why or 'verification failed'}",))
        return new

    @staticmethod
    def _stop(state: TaskCheckpoint, reason: str, *, extra: tuple[str, ...] = ()) -> TaskCheckpoint:
        return replace(state, status=TaskStatus.STOPPED, stop_reason=reason,
                       unresolved_issues=tuple(dict.fromkeys((*state.unresolved_issues, *extra, reason))))

    @classmethod
    def _reject(cls, state: TaskCheckpoint, action: TaskAction, fingerprint: str, reason: str,
                actual_target: str | None = None) -> TaskCheckpoint:
        rec = StepRecord(len(state.steps)+1, action.action_id, action.name, action.target, actual_target,
                         None, False, False, False, reason=reason)
        return cls._stop(replace(state, steps=(*state.steps, rec), scene_fingerprint=fingerprint,
                                 pending_action=None, approved_action_id=None), reason)


def validate_semantic_target(action: TaskAction, scene: object) -> Validation:
    try:
        from app.agent.perception.target_resolver import TargetResolver
        resolved = TargetResolver().resolve(scene, action.target)
    except (AttributeError, TypeError, ValueError) as exc: return Validation(False, reason=f"target_resolution_failed:{type(exc).__name__}")
    return Validation(bool(resolved.resolved and resolved.element is not None),
                      getattr(resolved.element, "label", None), resolved.reason, resolved.element)


def fingerprint_scene(scene: object) -> str:
    obs = getattr(scene, "observation", None); state = getattr(obs, "state", None)
    elements = []
    allowed = ("current_value", "uia_selected", "document_scope", "enabled", "is_enabled", "checked", "selected",
               "semantic_label", "semantic_name", "uia_owned_modal", "uia_tab_scope", "source", "role", "name")
    for e in getattr(scene, "elements", ()) or ():
        meta = getattr(e, "metadata", {}) or {}
        elements.append({"kind": _value(getattr(e, "kind", None)), "label": getattr(e, "label", None),
                         "capability": _value(getattr(e, "interaction_capability", None)),
                         "confidence": getattr(e, "confidence", None),
                         "state": {k: _plain(meta[k]) for k in allowed if k in meta}})
    payload = {"application": getattr(state, "active_application", None),
               "window_title": getattr(state, "active_window_title", None),
               "active_document": getattr(scene, "active_document", None),
               "elements": sorted(elements, key=lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True, default=str))}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _plain(value):
    if isinstance(value, Enum): return value.value
    if isinstance(value, Mapping): return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)): return [_plain(x) for x in value]
    if value is None or isinstance(value, (str, int, float, bool)): return value
    return str(value)


def _action_payload(a: TaskAction) -> dict[str, object]:
    return {"action_id": a.action_id, "name": a.name, "target": a.target,
            "scene_fingerprint": a.scene_fingerprint, "value": a.value,
            "expected_state": _plain(a.expected_state), "requires_confirmation": a.requires_confirmation,
            "submission": a.submission}


def _action_from_payload(p: Mapping[str, object]) -> TaskAction:
    expected = p.get("expected_state") or {}
    if not isinstance(expected, Mapping): raise ValueError("expected_state must be an object.")
    return TaskAction(str(p["action_id"]), str(p["name"]), str(p["target"]), str(p["scene_fingerprint"]),
                      _optional_str(p.get("value")), dict(expected), bool(p.get("requires_confirmation", False)),
                      bool(p.get("submission", False)))


def _value(value): return getattr(value, "value", value)


def _optional_str(value): return value if isinstance(value, str) else None
