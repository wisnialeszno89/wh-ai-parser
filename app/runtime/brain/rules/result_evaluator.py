from app.runtime.agent.agent_state import AgentState
from app.runtime.brain.decision import Decision
from app.runtime.brain.decision_type import DecisionType
from app.runtime.brain.rules.retry_rule import RetryRule
from app.runtime.brain.rules.stop_rule import StopRule
from app.runtime.brain.rules.success_rule import SuccessRule


class ResultEvaluator:

    def __init__(
        self,
    ):

        self.rules = sorted(
            [
                SuccessRule(),
                RetryRule(),
                StopRule(),
            ],
            key=lambda rule: rule.priority,
        )

    def evaluate(
        self,
        state: AgentState,
    ) -> Decision:

        for rule in self.rules:

            decision = rule.evaluate(
                state,
            )

            if decision is not None:
                return decision

        return Decision(
            decision_type=DecisionType.CONTINUE,
        )