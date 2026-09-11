from dataclasses import dataclass

from app.agent.agent_action import AgentAction


@dataclass(frozen=True)
class ActionStep:
    """
    One step inside an ActionPlan.
    """

    index: int

    action: AgentAction
