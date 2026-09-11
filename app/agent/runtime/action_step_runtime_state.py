from dataclasses import dataclass

from app.agent.runtime.action_step_status import (
    ActionStepStatus,
)


@dataclass(frozen=True)
class ActionStepRuntimeState:
    """
    Represents the current runtime state of a single
    action step.

    Unlike ActionStepTransition, which represents one
    historical state change, this object represents the
    latest known state of a step during execution.

    The runtime state is intended to support:

    - execution monitoring
    - failure recovery
    - checkpointing
    - execution resume
    - runtime inspection
    """

    step_index: int

    action_name: str

    status: ActionStepStatus

    attempts: int = 0

    last_error: str = ""

    @property
    def is_terminal(self) -> bool:
        """
        Return whether this step reached a terminal state.
        """

        return self.status in (
            ActionStepStatus.COMPLETED,
            ActionStepStatus.SKIPPED,
            ActionStepStatus.STOPPED,
            ActionStepStatus.MANUAL_REVIEW,
        )

    @property
    def can_resume(self) -> bool:
        """
        Return whether execution may potentially continue
        from this step.

        Terminal successful or explicitly skipped steps
        do not require resuming.
        """

        return self.status in (
            ActionStepStatus.PENDING,
            ActionStepStatus.PREPARING,
            ActionStepStatus.READY,
            ActionStepStatus.EXECUTING,
            ActionStepStatus.VERIFYING,
            ActionStepStatus.FAILED,
        )
