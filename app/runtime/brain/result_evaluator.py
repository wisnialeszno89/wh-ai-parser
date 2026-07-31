from app.runtime.agent.agent_state import AgentState
from app.runtime.brain.decision import Decision
from app.runtime.brain.decision_type import DecisionType
from app.runtime.brain.failure_type import FailureType


class ResultEvaluator:
    """
    Evaluates the outcome of the last executed action.
    """

    def evaluate(
        self,
        state: AgentState,
    ) -> Decision:

        result = state.last_result

        if result is None:
            return Decision(
                decision_type=DecisionType.CONTINUE,
            )

        if result.success:
            return Decision(
                decision_type=DecisionType.CONTINUE,
                reason="Action succeeded.",
            )

        if result.failure_type == FailureType.PERMANENT:
            return Decision(
                decision_type=DecisionType.STOP,
                reason=result.message,
            )

        if (
            result.failure_type == FailureType.TRANSIENT
            and state.can_retry
        ):
            return Decision(
                decision_type=DecisionType.RETRY,
                reason=(
                    f"Retry "
                    f"{state.retry_count + 1}/"
                    f"{state.mission.retry_limit}: "
                    f"{result.message}"
                ),
            )

        return Decision(
            decision_type=DecisionType.STOP,
            reason=result.message,
        )