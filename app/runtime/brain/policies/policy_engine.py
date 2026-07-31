from app.runtime.agent.agent_state import AgentState
from app.runtime.brain.decision import Decision
from app.runtime.brain.policies.skip_active_tool_policy import (
    SkipActiveToolPolicy,
)


class PolicyEngine:

    def __init__(
        self,
    ):

        self.policies = sorted(
            [
                SkipActiveToolPolicy(),
            ],
            key=lambda policy: policy.priority,
        )

    def evaluate(
        self,
        state: AgentState,
    ) -> Decision | None:

        for policy in self.policies:

            decision = policy.evaluate(
                state,
            )

            if decision is not None:
                return decision

        return None