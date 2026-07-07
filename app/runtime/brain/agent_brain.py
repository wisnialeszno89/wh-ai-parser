from app.runtime.agent.agent_state import AgentState


class AgentBrain:

    def next_action(
        self,
        state: AgentState,
    ):

        if state.current_step >= len(state.mission.gui_plan.actions):
            return None

        return state.mission.gui_plan.actions[state.current_step]

    def think(
        self,
        state: AgentState,
    ):

        print()

        print("[WORLD]")
        print(f"Objects: {len(state.world.objects)}")
        print(f"Toolbar: {state.world.toolbar_visible}")
        print(f"Active: {state.world.active_tool}")

        print()

        print("[BRAIN]")

        if state.last_result.success:
            print(f"[OK] {state.last_result.message}")
            return "continue"

        print(f"[FAIL] {state.last_result.message}")

        return "retry"