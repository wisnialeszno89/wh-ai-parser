from app.runtime.agent.agent_state import AgentState
from app.runtime.brain.decision import Decision
from app.runtime.brain.policies.policy_engine import PolicyEngine


class DecisionEngine:

    def __init__(self):

        self.policy_engine = PolicyEngine()

    def decide(
        self,
        state: AgentState,
    ) -> Decision:

        #
        # Najpierw wszystkie polityki.
        #

        decision = self.policy_engine.evaluate(
            state
        )

        if decision is not None:

            return decision

        #
        # Standardowa ścieżka wykonania.
        #

        if (
            state.current_step
            >= len(
                state.mission.gui_plan.actions
            )
        ):

            return Decision(
                action=None,
                reason="Mission completed",
            )

        action = (
            state.mission.gui_plan.actions[
                state.current_step
            ]
        )

        return Decision(
            action=action,
            reason="Next planned action",
        )