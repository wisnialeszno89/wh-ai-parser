from enum import Enum


class ActionStepStatus(
    str,
    Enum,
):
    """
    Lifecycle state of a single action step.

    The status describes the current execution state
    of the step independently from the overall plan.
    """

    PENDING = "pending"

    PREPARING = "preparing"

    READY = "ready"

    EXECUTING = "executing"

    VERIFYING = "verifying"

    COMPLETED = "completed"

    FAILED = "failed"

    SKIPPED = "skipped"

    MANUAL_REVIEW = "manual_review"

    STOPPED = "stopped"
