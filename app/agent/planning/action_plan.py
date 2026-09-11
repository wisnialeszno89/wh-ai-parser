from dataclasses import dataclass

from app.agent.agent_intent import AgentIntent
from app.agent.planning.action_step import ActionStep


@dataclass(frozen=True)
class ActionPlan:
    """
    Ordered semantic plan created by the agent.

    A plan is not execution.
    Execution will be handled later by controlled tools.
    """

    intent: AgentIntent

    steps: tuple[ActionStep, ...]

    confidence: float

    requires_manual_review: bool = False
