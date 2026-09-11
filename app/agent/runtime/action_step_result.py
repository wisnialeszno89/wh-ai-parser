from dataclasses import dataclass

from app.agent.runtime.action_step_status import (
    ActionStepStatus,
)


@dataclass(frozen=True)
class ActionStepResult:
    """
    Final outcome of one action step.

    This represents the semantic result of processing
    a single plan step, independently from whether
    the overall control loop succeeded.
    """

    action_name: str

    status: ActionStepStatus

    reason: str = ""

    attempts: int = 0
