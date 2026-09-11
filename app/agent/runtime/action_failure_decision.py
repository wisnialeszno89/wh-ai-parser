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

    SKIP = "skip"

    MANUAL_REVIEW = "manual_review"
