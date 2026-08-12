from app.runtime.agent.agent_state import AgentState

from app.runtime.brain.agent_brain import AgentBrain
from app.runtime.brain.decision_type import DecisionType

from app.runtime.execution.action_executor import ActionExecutor

from app.runtime.orchestrator.runtime_status import RuntimeStatus

from app.runtime.recovery.recovery_engine import RecoveryEngine

from app.runtime.world.perception_engine import PerceptionEngine

from app.runtime.mission.mission_step import MissionStep


class RuntimeOrchestrator:

    def __init__(
        self,
        executor: ActionExecutor,
        brain: AgentBrain,
        recovery: RecoveryEngine,
        perception: PerceptionEngine,
    ):

        self.executor = executor

        self.brain = brain

        self.recovery = recovery

        self.perception = perception

    def run_cycle(
        self,
        state: AgentState,
    ) -> RuntimeStatus:

        #
        # Ask Brain what to do.
        #

        decision = self.brain.next_action(
            state,
        )

        #
        # Mission finished.
        #

        if decision.action is None:

            return RuntimeStatus.FINISHED

        #
        # Skip action.
        #

        if (
            decision.decision_type
            == DecisionType.SKIP
        ):

            print(
                f"[SKIP] {decision.reason}"
            )

            state.next_step()

            return RuntimeStatus.RUNNING

        action = decision.action

        state.last_action = action

        #
        # Execute action.
        #

        result = self.executor.execute(
            action,
        )

        state.trace.add_step(

            MissionStep(

                action=action,

                result=result,

                duration_ms=result.duration_ms,

            )

        )

        state.last_result = result

        #
        # Refresh world.
        #

        state.world = (
            self.perception.perceive()
        )

        #
        # Evaluate execution.
        #

        brain_decision = self.brain.think(
            state,
        )

        #
        # Recovery.
        #

        if (
            brain_decision.decision_type
            == DecisionType.RECOVER
        ):

            print(
                f"[RECOVER] {brain_decision.recovery_type.value}"
            )

            self.recovery.recover(

                state,

                brain_decision.recovery_type,

            )

            state.increment_retry()

            return RuntimeStatus.RUNNING

        #
        # Retry.
        #

        if (
            brain_decision.decision_type
            == DecisionType.RETRY
        ):

            print(
                f"[RETRY] {brain_decision.reason}"
            )

            state.increment_retry()

            return RuntimeStatus.RUNNING

        #
        # Stop mission.
        #

        if (
            brain_decision.decision_type
            == DecisionType.STOP
        ):

            print(
                f"[STOP] {brain_decision.reason}"
            )

            return RuntimeStatus.FAILED

        #
        # Continue.
        #

        state.reset_retry()

        state.next_step()

        return RuntimeStatus.RUNNING