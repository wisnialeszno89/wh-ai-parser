from dataclasses import dataclass

from app.agent.runtime.action_failure_decision import (
    ActionFailureDecision,
)


@dataclass(frozen=True)
class ActionFailureRecord:
    """
    Records a failed action and the decision taken
    by the action failure policy.

    The record allows the control loop to preserve
    failure history while continuing execution when
    the policy allows it.
    """

    action_name: str

    reason: str

    attempts: int

    decision: ActionFailureDecision
