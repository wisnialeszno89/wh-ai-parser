from dataclasses import dataclass

from app.agent.decision.decision import (
    Decision,
)

from app.agent.runtime.action_failure_record import (
    ActionFailureRecord,
)

from app.agent.runtime.action_plan_status import (
    ActionPlanStatus,
)

from app.agent.runtime.action_plan_transition import (
    ActionPlanTransition,
)

from app.agent.runtime.action_step_result import (
    ActionStepResult,
)

from app.agent.runtime.action_step_transition import (
    ActionStepTransition,
)

from app.agent.runtime.action_step_runtime_state import (
    ActionStepRuntimeState,
)

from app.agent.runtime.execution_loop_result import (
    ExecutionLoopResult,
)


@dataclass(frozen=True)
class ControlLoopResult:
    """
    Aggregated result of controlling an entire action plan.

    The result records:

    - decisions made before actions
    - execution feedback loop results
    - final semantic result of every processed step
    - lifecycle transition history
    - execution failures
    - whether execution completed successfully
    - whether manual review is required
    """

    decisions: tuple[Decision, ...]

    plan_status: ActionPlanStatus

    execution_results: tuple[
        ExecutionLoopResult,
        ...
    ]

    success: bool

    plan_transitions: tuple[
        ActionPlanTransition,
        ...
    ] = ()

    step_results: tuple[
        ActionStepResult,
        ...
    ] = ()

    step_transitions: tuple[
        ActionStepTransition,
        ...
    ] = ()


    runtime_states: tuple[
        ActionStepRuntimeState,
        ...
    ] = ()

    failure_records: tuple[
        ActionFailureRecord,
        ...
    ] = ()

    requires_manual_review: bool = False

    stopped: bool = False

    @property
    def failed_actions(self) -> int:
        """
        Number of actions that produced a recorded
        execution failure.
        """

        return len(
            self.failure_records
        )

    @property
    def skipped_actions(self) -> int:
        """
        Number of failed actions explicitly skipped
        by the failure policy.
        """

        from app.agent.runtime.action_failure_decision import (
            ActionFailureDecision,
        )

        return sum(
            1
            for record in self.failure_records
            if (
                record.decision
                == ActionFailureDecision.SKIP
            )
        )

    @property
    def executed_actions(self) -> int:
        """
        Number of actions that entered the execution loop.
        """

        return len(
            self.execution_results
        )

    @property
    def last_execution_result(
        self,
    ) -> ExecutionLoopResult | None:

        if not self.execution_results:
            return None

        return self.execution_results[-1]

    @property
    def transition_count(self) -> int:
        """
        Number of recorded lifecycle transitions.
        """

        return len(
            self.step_transitions
        )


    def get_runtime_state(
        self,
        step_index: int,
    ) -> ActionStepRuntimeState | None:
        """
        Return the latest runtime state for the
        requested action step.
        """

        for state in self.runtime_states:

            if state.step_index == step_index:

                return state

        return None
