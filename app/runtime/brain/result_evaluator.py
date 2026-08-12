from app.runtime.agent.agent_state import AgentState

from app.runtime.brain.decision import Decision

from app.runtime.brain.rules.decision_rule import DecisionRule
from app.runtime.brain.rules.success_rule import SuccessRule
from app.runtime.brain.rules.wait_rule import WaitRule
from app.runtime.brain.rules.recovery_rule import RecoveryRule
from app.runtime.brain.rules.retry_rule import RetryRule
from app.runtime.brain.rules.stop_rule import StopRule


class ResultEvaluator:
    """
    Evaluates the outcome of the last executed action.

    Rules are evaluated by priority.
    The first matching rule returns the Decision.
    """

    def __init__(self):

        self.rules: list[DecisionRule] = sorted(
            [
                SuccessRule(),
                WaitRule(),
                RecoveryRule(),
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

        #
        # This should never happen because StopRule
        # always returns a Decision.
        #

        raise RuntimeError(
            "No DecisionRule returned a Decision."
        )