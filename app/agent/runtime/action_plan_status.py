from enum import Enum


class ActionPlanStatus(
    str,
    Enum,
):
    """
    Lifecycle status of an entire action plan.
    """

    CREATED = "created"

    RUNNING = "running"

    COMPLETED = "completed"

    FAILED = "failed"

    STOPPED = "stopped"

    MANUAL_REVIEW = "manual_review"
