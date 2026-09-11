from app.agent.runtime.action_step_status import (
    ActionStepStatus,
)


class ActionStepLifecycle:
    """
    Defines valid lifecycle transitions for an action step.

    The lifecycle is intentionally independent from the
    AgentControlLoop.

    Its responsibility is limited to one question:

        Can a step move from status A to status B?

    This creates a stable state machine that can later be
    reused by:

    - control loop execution
    - recovery logic
    - checkpoint persistence
    - plan resume
    - execution history
    """

    _TERMINAL_STATUSES = frozenset(
        {
            ActionStepStatus.COMPLETED,
            ActionStepStatus.SKIPPED,
            ActionStepStatus.MANUAL_REVIEW,
            ActionStepStatus.STOPPED,
        }
    )

    _TRANSITIONS = {
        ActionStepStatus.PENDING: frozenset(
            {
                ActionStepStatus.PREPARING,
                ActionStepStatus.SKIPPED,
                ActionStepStatus.MANUAL_REVIEW,
                ActionStepStatus.STOPPED,
            }
        ),

        ActionStepStatus.PREPARING: frozenset(
            {
                ActionStepStatus.READY,
                ActionStepStatus.FAILED,
                ActionStepStatus.MANUAL_REVIEW,
                ActionStepStatus.STOPPED,
            }
        ),

        ActionStepStatus.READY: frozenset(
            {
                ActionStepStatus.EXECUTING,
                ActionStepStatus.SKIPPED,
                ActionStepStatus.MANUAL_REVIEW,
                ActionStepStatus.STOPPED,
            }
        ),

        ActionStepStatus.EXECUTING: frozenset(
            {
                ActionStepStatus.VERIFYING,
                ActionStepStatus.FAILED,
                ActionStepStatus.MANUAL_REVIEW,
                ActionStepStatus.STOPPED,
            }
        ),

        ActionStepStatus.VERIFYING: frozenset(
            {
                ActionStepStatus.COMPLETED,
                ActionStepStatus.FAILED,
                ActionStepStatus.MANUAL_REVIEW,
                ActionStepStatus.STOPPED,
            }
        ),

        ActionStepStatus.FAILED: frozenset(
            {
                ActionStepStatus.SKIPPED,
                ActionStepStatus.MANUAL_REVIEW,
                ActionStepStatus.STOPPED,
            }
        ),

        ActionStepStatus.COMPLETED: frozenset(),

        ActionStepStatus.SKIPPED: frozenset(),

        ActionStepStatus.MANUAL_REVIEW: frozenset(),

        ActionStepStatus.STOPPED: frozenset(),
    }

    def can_transition(
        self,
        current: ActionStepStatus,
        target: ActionStepStatus,
    ) -> bool:
        """
        Return whether a transition is valid.
        """

        if current == target:
            return False

        return target in self._TRANSITIONS[
            current
        ]

    def transition(
        self,
        current: ActionStepStatus,
        target: ActionStepStatus,
    ) -> ActionStepStatus:
        """
        Validate and perform a lifecycle transition.

        Returns the target status when the transition
        is valid.

        Raises ValueError when the transition is invalid.
        """

        if not self.can_transition(
            current,
            target,
        ):
            raise ValueError(
                "Invalid action step status "
                f"transition: {current.value} "
                f"-> {target.value}"
            )

        return target

    def is_terminal(
        self,
        status: ActionStepStatus,
    ) -> bool:
        """
        Return whether a status represents the end of
        the current step lifecycle.
        """

        return status in self._TERMINAL_STATUSES

    def allowed_transitions(
        self,
        status: ActionStepStatus,
    ) -> tuple[ActionStepStatus, ...]:
        """
        Return all statuses reachable directly from
        the current status.
        """

        return tuple(
            self._TRANSITIONS[status]
        )
