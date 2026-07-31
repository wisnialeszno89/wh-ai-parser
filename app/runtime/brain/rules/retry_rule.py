from app.runtime.agent.agent_state import AgentState
from app.runtime.brain.decision import Decision
from app.runtime.brain.decision_type import DecisionType
from app.runtime.brain.failure_type import FailureType
from app.runtime.brain.rules.decision_rule import DecisionRule


class RetryRule(DecisionRule):

    priority = 20

    def evaluate(
        self,
        state: AgentState,
    ) -> Decision | None:

        result = state.last_result

        if result is None:
            return None

        if result.failure_type != FailureType.TRANSIENT:
            return None

        if not state.can_retry:
            return None

        return Decision(
            decision_type=DecisionType.RETRY,
            reason=(
                f"Retry "
                f"{state.retry_count + 1}/"
                f"{state.mission.retry_limit}: "
                f"{result.message}"
            ),
        )