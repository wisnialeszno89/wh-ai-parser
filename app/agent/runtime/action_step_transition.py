from dataclasses import dataclass

from app.agent.runtime.action_step_status import (
    ActionStepStatus,
)


@dataclass(frozen=True)
class ActionStepTransition:
    """
    Records one lifecycle transition of an action step.

    The transition represents a real state change during
    plan execution.

    It is intentionally separate from ActionStepResult:

    - ActionStepResult describes the final outcome
    - ActionStepTransition describes the execution path
    """

    action_name: str

    from_status: ActionStepStatus

    to_status: ActionStepStatus
