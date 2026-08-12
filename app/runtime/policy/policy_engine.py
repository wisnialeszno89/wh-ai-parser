from app.runtime.agent.agent_state import AgentState


class PolicyEngine:
    """
    Selects the next GUI action to execute.
    """

    def next_action(
        self,
        state: AgentState,
    ):

        actions = state.mission.gui_plan.actions

        if state.current_step >= len(actions):
            return None

        return actions[state.current_step]