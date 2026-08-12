from app.runtime.agent.agent_state import AgentState

from app.runtime.brain.decision import Decision
from app.runtime.brain.decision_type import DecisionType

from app.runtime.brain.rules.decision_rule import DecisionRule


class StopRule(DecisionRule):
    """
    Final fallback rule.

    If no previous rule matched, the mission is stopped.
    """

    priority = 1000

    def evaluate(
        self,
        state: AgentState,
    ) -> Decision | None:

        result = state.last_result

        if result is None:

            return Decision(
                decision_type=DecisionType.STOP,
                reason="No action result available.",
            )

        return Decision(
            decision_type=DecisionType.STOP,
            reason=result.message or "Mission stopped.",
        )