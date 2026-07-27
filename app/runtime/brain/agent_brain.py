from app.runtime.agent.agent_state import AgentState
from app.runtime.brain.decision_engine import DecisionEngine


class AgentBrain:

    def __init__(self):

        self.decision_engine = DecisionEngine()

    def next_action(
        self,
        state: AgentState,
    ):

        #
        # Zwraca pełną decyzję.
        #

        return self.decision_engine.decide(
            state
        )

    def think(
        self,
        state: AgentState,
    ):

        print()

        print("[WORLD]")

        print(
            f"Objects: {len(state.world.objects)}"
        )

        print(
            f"Toolbar: {state.world.toolbar_visible}"
        )

        print(
            f"Active: {state.world.active_tool}"
        )

        print()

        print("[BRAIN]")

        if state.last_result.success:

            print(
                f"[OK] {state.last_result.message}"
            )

            return "continue"

        print(
            f"[FAIL] {state.last_result.message}"
        )

        return "retry"