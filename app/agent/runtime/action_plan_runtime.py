from app.agent.planning.action_plan import (
    ActionPlan,
)

from app.agent.runtime.action_plan_runtime_state import (
    ActionPlanRuntimeState,
)

from app.agent.runtime.action_step_runtime_state import (
    ActionStepRuntimeState,
)

from app.agent.runtime.action_step_status import (
    ActionStepStatus,
)


class ActionPlanRuntime:
    """
    Runtime controller for an ActionPlan.

    This object owns the mutable execution state of a plan.

    Responsibilities:

    - track runtime state for every action step
    - track the current active step
    - expose aggregate plan runtime state
    - provide controlled step status updates
    - determine whether the plan is complete
    - determine whether the plan succeeded
    - detect stopped and manual-review states

    The AgentControlLoop coordinates execution.

    ActionPlanRuntime coordinates runtime state.
    """

    def __init__(
        self,
        plan: ActionPlan,
    ) -> None:

        self.plan = plan

        self._step_states = {
            step.index: ActionStepRuntimeState(
                step_index=step.index,
                action_name=step.action.name,
            )
            for step in plan.steps
        }

        self._current_step_index: int | None = None

    # ---------------------------------
    # STEP ACCESS
    # ---------------------------------

    @property
    def step_states(
        self,
    ) -> tuple[ActionStepRuntimeState, ...]:
        """
        Return runtime states in plan order.
        """

        return tuple(
            self._step_states[step.index]
            for step in self.plan.steps
        )

    def get_step_state(
        self,
        step_index: int,
    ) -> ActionStepRuntimeState:
        """
        Return runtime state for one step.
        """

        try:
            return self._step_states[
                step_index
            ]
        except KeyError:

            raise ValueError(
                f"Unknown action step index: "
                f"{step_index}"
            )

    @property
    def current_step_index(
        self,
    ) -> int | None:
        """
        Index of the currently active step.
        """

        return self._current_step_index

    @property
    def current_step(
        self,
    ) -> ActionStepRuntimeState | None:
        """
        Runtime state of the current step.
        """

        if (
            self._current_step_index
            is None
        ):
            return None

        return self.get_step_state(
            self._current_step_index
        )

    # ---------------------------------
    # STEP STATE CHANGES
    # ---------------------------------

    def start_step(
        self,
        step_index: int,
    ) -> ActionStepRuntimeState:
        """
        Mark a step as the currently active step.

        Starting a step does not automatically imply
        execution. The caller still controls lifecycle
        progression such as READY -> EXECUTING.
        """

        state = self.get_step_state(
            step_index
        )

        if state.is_terminal:
            raise ValueError(
                f"Cannot start terminal step: "
                f"{step_index}"
            )

        self._current_step_index = (
            step_index
        )

        return state

    def update_step(
        self,
        step_index: int,
        status: ActionStepStatus,
        reason: str = "",
    ) -> ActionStepRuntimeState:
        """
        Update the runtime state of one action step.

        ActionStepRuntimeState remains responsible
        for validating lifecycle transitions.
        """

        state = self.get_step_state(
            step_index
        )

        updated_state = (
            state.transition_to(
                status,
                reason=reason,
            )
        )

        self._step_states[
            step_index
        ] = updated_state

        if updated_state.is_terminal:
            if (
                self._current_step_index
                == step_index
            ):
                self._current_step_index = None

        return updated_state

    # ---------------------------------
    # CONVENIENCE TRANSITIONS
    # ---------------------------------

    def mark_ready(
        self,
        step_index: int,
    ) -> ActionStepRuntimeState:

        return self.update_step(
            step_index,
            ActionStepStatus.READY,
        )

    def mark_executing(
        self,
        step_index: int,
    ) -> ActionStepRuntimeState:

        return self.update_step(
            step_index,
            ActionStepStatus.EXECUTING,
        )

    def mark_verifying(
        self,
        step_index: int,
    ) -> ActionStepRuntimeState:

        return self.update_step(
            step_index,
            ActionStepStatus.VERIFYING,
        )

    def mark_completed(
        self,
        step_index: int,
    ) -> ActionStepRuntimeState:

        return self.update_step(
            step_index,
            ActionStepStatus.COMPLETED,
        )

    def mark_skipped(
        self,
        step_index: int,
        reason: str = "",
    ) -> ActionStepRuntimeState:

        return self.update_step(
            step_index,
            ActionStepStatus.SKIPPED,
            reason=reason,
        )

    def mark_failed(
        self,
        step_index: int,
        reason: str = "",
    ) -> ActionStepRuntimeState:

        return self.update_step(
            step_index,
            ActionStepStatus.FAILED,
            reason=reason,
        )

    def mark_stopped(
        self,
        step_index: int,
        reason: str = "",
    ) -> ActionStepRuntimeState:

        return self.update_step(
            step_index,
            ActionStepStatus.STOPPED,
            reason=reason,
        )

    def require_manual_review(
        self,
        step_index: int,
        reason: str = "",
    ) -> ActionStepRuntimeState:

        return self.update_step(
            step_index,
            ActionStepStatus.MANUAL_REVIEW,
            reason=reason,
        )

    # ---------------------------------
    # AGGREGATE STATE
    # ---------------------------------

    @property
    def state(
        self,
    ) -> ActionPlanRuntimeState:
        """
        Build aggregate runtime state for the plan.
        """

        states = self.step_states

        return ActionPlanRuntimeState(
            step_states=states,
        )

    @property
    def is_complete(
        self,
    ) -> bool:
        """
        True when every plan step reached a terminal state.
        """

        return self.state.is_complete

    @property
    def is_successful(
        self,
    ) -> bool:
        """
        True when the plan completed successfully.
        """

        return self.state.is_successful

    @property
    def requires_manual_review(
        self,
    ) -> bool:
        """
        True when any step requires manual review.
        """

        return self.state.requires_manual_review

    @property
    def is_stopped(
        self,
    ) -> bool:
        """
        True when execution has been explicitly stopped.
        """

        return self.state.is_stopped
