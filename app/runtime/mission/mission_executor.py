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

from app.runtime.mission.mission_logger import (
    MissionLogger,
)

from app.runtime.mission.mission_step import (
    MissionStep,
)

from app.runtime.mission.mission_trace import (
    MissionTrace,
)

from app.runtime.world.perception_engine import (
    PerceptionEngine,
)
from app.runtime.brain.decision_type import DecisionType

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

        self.logger = MissionLogger()

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

                state.next_step()

                continue

            action = decision.action

            state.last_action = action

            #
            # Execute GUI action.
            #

            result = self.executor.execute(
                action,
            )

            #
            # Save mission trace.
            #

            state.trace.add_step(

                MissionStep(

                    action=action,

                    result=result,

                )

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

            if (
                brain_decision.decision_type
                == DecisionType.RETRY
            ):

                print(
                    f"[RETRY] {brain_decision.reason}"
                )

                state.increment_retry()

                continue

            if (
                brain_decision.decision_type
                == DecisionType.STOP
            ):

                print(
                f"[STOP] {brain_decision.reason}"
            )

            break

        state.reset_retry()

        state.next_step()

        state.finish()

        #
        # Print mission summary.
        #

        self.logger.print(
            state.trace,
        )       

        return state