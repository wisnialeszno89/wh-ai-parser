from app.agent.runtime.action_plan_status import (
    ActionPlanStatus,
)

from app.agent.runtime.action_plan_transition import (
    ActionPlanTransition,
)


class ActionPlanLifecycle:
    """
    Stateful lifecycle controller for an entire action plan.

    The lifecycle is intentionally explicit so that the
    runtime can reason about valid plan-level transitions.
    """

    _allowed_transitions = {
        ActionPlanStatus.CREATED: {
            ActionPlanStatus.RUNNING,
            ActionPlanStatus.STOPPED,
        },

        ActionPlanStatus.RUNNING: {
            ActionPlanStatus.COMPLETED,
            ActionPlanStatus.FAILED,
            ActionPlanStatus.STOPPED,
            ActionPlanStatus.MANUAL_REVIEW,
        },

        ActionPlanStatus.COMPLETED: set(),
        ActionPlanStatus.FAILED: set(),
        ActionPlanStatus.STOPPED: set(),
        ActionPlanStatus.MANUAL_REVIEW: set(),
    }

    def __init__(
        self,
        status: ActionPlanStatus = (
            ActionPlanStatus.CREATED
        ),
    ) -> None:

        self._status = status

        self._transitions: list[
            ActionPlanTransition
        ] = []

    @property
    def status(self) -> ActionPlanStatus:

        return self._status

    @property
    def transitions(
        self,
    ) -> tuple[ActionPlanTransition, ...]:

        return tuple(
            self._transitions
        )

    def can_transition_to(
        self,
        status: ActionPlanStatus,
    ) -> bool:

        return (
            status
            in self._allowed_transitions[
                self._status
            ]
        )

    def transition_to(
        self,
        status: ActionPlanStatus,
        reason: str = "",
    ) -> ActionPlanTransition:
        """
        Move the plan to a new lifecycle state.

        Raises ValueError when the transition is invalid.
        """

        if not self.can_transition_to(
            status
        ):
            raise ValueError(
                "Invalid action plan lifecycle "
                f"transition: {self._status} "
                f"-> {status}"
            )

        transition = (
            ActionPlanTransition(
                from_status=self._status,
                to_status=status,
                reason=reason,
            )
        )

        self._transitions.append(
            transition
        )

        self._status = status

        return transition

    @property
    def is_terminal(self) -> bool:

        return (
            self._status
            in {
                ActionPlanStatus.COMPLETED,
                ActionPlanStatus.FAILED,
                ActionPlanStatus.STOPPED,
                ActionPlanStatus.MANUAL_REVIEW,
            }
        )
