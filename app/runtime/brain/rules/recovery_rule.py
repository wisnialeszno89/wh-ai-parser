from app.runtime.agent.agent_state import AgentState
from app.runtime.brain.decision import Decision
from app.runtime.brain.decision_type import DecisionType
from app.runtime.brain.failure_type import FailureType
from app.runtime.brain.recovery_type import RecoveryType
from app.runtime.brain.rules.decision_rule import DecisionRule


class RecoveryRule(DecisionRule):

    priority = 15

    def evaluate(
        self,
        state: AgentState,
    ) -> Decision | None:

        result = state.last_result

        if result is None:
            return None

        if result.failure_type != FailureType.UNKNOWN:
            return None

        if state.retry_count > 0:
            return None

        return Decision(
            decision_type=DecisionType.RECOVER,
            recovery_type=RecoveryType.REFRESH_WORLD,
            reason="Refresh world before retry.",
        )