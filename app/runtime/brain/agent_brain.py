from app.runtime.agent.agent_state import AgentState
from app.runtime.brain.decision import Decision
from app.runtime.brain.decision_engine import DecisionEngine
from app.runtime.brain.result_evaluator import ResultEvaluator


class AgentBrain:

    def __init__(
        self,
    ):

        self.decision_engine = DecisionEngine()

        self.result_evaluator = ResultEvaluator()

    def next_action(
        self,
        state: AgentState,
    ) -> Decision:

        return self.decision_engine.decide(
            state,
        )

    def think(
        self,
        state: AgentState,
    ) -> Decision:

        self._print_world(
            state,
        )

        return self.result_evaluator.evaluate(
            state,
        )

    def _print_world(
        self,
        state: AgentState,
    ) -> None:

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