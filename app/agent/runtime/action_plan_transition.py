from dataclasses import dataclass

from app.agent.runtime.action_plan_status import (
    ActionPlanStatus,
)


@dataclass(frozen=True)
class ActionPlanTransition:
    """
    One transition in the lifecycle of an action plan.
    """

    from_status: ActionPlanStatus

    to_status: ActionPlanStatus

    reason: str = ""
