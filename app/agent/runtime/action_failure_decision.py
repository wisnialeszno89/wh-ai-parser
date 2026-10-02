from enum import Enum


class ActionFailureDecision(
    str,
    Enum,
):
    """
    Describes what the runtime should do after
    an action execution failure.
    """

    STOP = "stop"

    CONTINUE = "continue"

    RETRY = "retry"

    REPLAN = "replan"

    SKIP = "skip"

    MANUAL_REVIEW = "manual_review"
