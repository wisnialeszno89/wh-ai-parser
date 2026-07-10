from app.runtime.agent.agent_state import AgentState
from app.runtime.brain.decision import Decision
from app.runtime.brain.policies.policy import Policy


class SkipActiveToolPolicy(Policy):

    def evaluate(
        self,
        state: AgentState,
    ) -> Decision | None:

        return None