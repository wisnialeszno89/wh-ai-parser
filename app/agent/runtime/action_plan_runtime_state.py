from dataclasses import dataclass

from app.agent.runtime.action_plan_status import (
    ActionPlanStatus,
)


@dataclass(frozen=True)
class ActionPlanRuntimeState:
    """
    Current runtime state of an entire action plan.

    The state provides a compact operational view of plan
    execution without replacing detailed step-level history.

    Step-level details remain owned by:

    - ActionStepRuntimeState
    - ActionStepTransition
    - ActionStepResult
    - ActionFailureRecord
    """

    status: ActionPlanStatus = (
        ActionPlanStatus.CREATED
    )

    current_step_index: int | None = None

    total_steps: int = 0

    completed_steps: int = 0

    failed_steps: int = 0

    skipped_steps: int = 0

    requires_manual_review: bool = False

    stopped: bool = False

    @property
    def is_finished(self) -> bool:
        """
        Whether the plan reached a terminal runtime state.
        """

        return (
            self.status
            in (
                ActionPlanStatus.COMPLETED,
                ActionPlanStatus.FAILED,
                ActionPlanStatus.STOPPED,
                ActionPlanStatus.MANUAL_REVIEW,
            )
        )

    @property
    def processed_steps(self) -> int:
        """
        Number of steps that reached a completed
        or terminal operational outcome.
        """

        return (
            self.completed_steps
            + self.failed_steps
            + self.skipped_steps
        )

    @property
    def remaining_steps(self) -> int:
        """
        Number of plan steps that remain unprocessed.
        """

        remaining = (
            self.total_steps
            - self.processed_steps
        )

        return max(
            remaining,
            0,
        )
