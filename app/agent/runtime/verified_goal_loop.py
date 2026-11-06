"""Fail-closed Observe/Act/Verify engine; no I/O without injected adapters."""
from dataclasses import dataclass
from typing import Callable, Any

@dataclass(frozen=True)
class GoalStep:
    action: str
    target: str
    expected: str
    value: str | None = None
    persistent: bool = False

@dataclass(frozen=True)
class GoalDecision:
    kind: str
    step: GoalStep | None = None

@dataclass(frozen=True)
class GoalResult:
    status: str
    reason: str
    actions: int
    observations: int
    trace: tuple

def run_verified_goal(
    *, observe: Callable[[], Any], decide: Callable,
    execute: Callable, verify_action: Callable,
    verify_goal: Callable, fingerprint: Callable,
    max_actions: int = 8, approve_persistent: bool = False,
) -> GoalResult:
    """Adapters own the Windows UI; postcondition checks own correctness."""
    if not 1 <= max_actions <= 50:
        raise ValueError("invalid_max_actions")
    trace = []
    actions = 0
    observations = 0
    def stop(status, reason):
        return GoalResult(status, reason, actions, observations, tuple(trace))
    try:
        scene = observe()
        observations += 1
        state = fingerprint(scene)
    except Exception:
        return stop("blocked", "initial_observation_failed")
    encountered = set()
    while True:
        try:
            if verify_goal(scene) is True:
                return stop("verified", "goal_postconditions_verified")
            proposal = decide(scene, tuple(trace))
        except Exception:
            return stop("blocked", "reasoner_or_goal_check_failed")
        if not isinstance(proposal, GoalDecision):
            return stop("blocked", "invalid_decision")
        if proposal.kind == "done":
            return stop("review", "done_without_goal_evidence")
        if proposal.kind == "review":
            return stop("review", "model_requested_review")
        if proposal.kind != "act" or not isinstance(proposal.step, GoalStep):
            return stop("blocked", "invalid_action")
        if actions >= max_actions:
            return stop("budget_exhausted", "action_budget_reached")
        step = proposal.step
        if not step.action or not step.target or not step.expected:
            return stop("blocked", "unverifiable_action")
        if step.persistent and not approve_persistent:
            return stop("review", "persistent_action_needs_approval")
        signature = (state, step.action, step.target, step.value, step.expected)
        if signature in encountered:
            return stop("review", "repeated_action_without_progress")
        encountered.add(signature)
        try:
            executed = execute(step)
        except Exception:
            return stop("blocked", "execution_raised")
        if executed is not True:
            return stop("blocked", "execution_not_confirmed")
        actions += 1
        try:
            after = observe()
            observations += 1
            new_state = fingerprint(after)
            verified = verify_action(step, scene, after) is True
        except Exception:
            return stop("review", "post_action_verification_failed")
        trace.append({"action": step.action, "target": step.target,
                      "verified": verified, "state_changed": new_state != state})
        if not verified:
            return stop("review", "action_postcondition_not_verified")
        scene, state = after, new_state
