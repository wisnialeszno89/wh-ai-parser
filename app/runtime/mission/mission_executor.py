from app.runtime.agent.agent_state import (
    AgentState,
)

from app.runtime.brain.agent_brain import (
    AgentBrain,
)

from app.runtime.execution.action_executor import (
    ActionExecutor,
)

from app.runtime.execution.context.execution_context import (
    ExecutionContext,
)

from app.runtime.mission.mission import (
    Mission,
)

from app.runtime.world.perception_engine import (
    PerceptionEngine,
)


class MissionExecutor:

    def __init__(
        self,
        context: ExecutionContext,
    ):

        self.executor = ActionExecutor(
            context,
        )

        self.brain = AgentBrain()

        self.perception = PerceptionEngine()

    def execute(
        self,
        mission: Mission,
    ):

        state = AgentState(
            mission,
        )

        while True:

            decision = self.brain.next_action(
                state,
            )

            #
            # Mission finished.
            #

            if (
                decision.action is None
                and not decision.skip
            ):
                break

            #
            # Policy skipped current step.
            #

            if decision.skip:

                print(
                    f"[SKIP] {decision.reason}"
                )

                state.current_step += 1

                continue

            action = decision.action

            state.last_action = action

            #
            # Execute GUI action.
            #

            result = self.executor.execute(
                action,
            )

            state.last_result = result

            #
            # Refresh world model.
            #

            state.world = (
                self.perception.perceive()
            )

            #
            # Let the brain evaluate the result.
            #

            brain_decision = self.brain.think(
                state,
            )

            if brain_decision == "retry":

                state.retry_count += 1

                continue

            state.retry_count = 0

            state.current_step += 1

        state.completed = True

        return state