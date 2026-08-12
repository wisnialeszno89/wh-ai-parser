from app.runtime.agent.agent_state import AgentState

from app.runtime.brain.decision import Decision
from app.runtime.brain.result_evaluator import ResultEvaluator

from app.runtime.policy.policy_engine import PolicyEngine


class AgentBrain:
    """
    Central decision-making component of the runtime.

    Responsibilities:

    - choose the next mission action
    - evaluate the result of the last action

    All decision logic is delegated to specialized components.
    """

    def __init__(self):

        self.policy_engine = PolicyEngine()

        self.result_evaluator = ResultEvaluator()

    def next_action(
        self,
        state: AgentState,
    ) -> Decision:

        action = self.policy_engine.next_action(
            state,
        )

        return Decision(
            action=action,
        )

    def think(
        self,
        state: AgentState,
    ) -> Decision:

        return self.result_evaluator.evaluate(
            state,
        )