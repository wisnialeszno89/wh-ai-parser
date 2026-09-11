from enum import Enum


class DecisionType(str, Enum):
    """
    High-level outcome of the agent decision process.

    The decision layer does not perform actions itself.
    It determines what should happen next.
    """

    PROCEED = "proceed"

    INTERACT = "interact"

    WAIT = "wait"

    MANUAL_REVIEW = "manual_review"

    STOP = "stop"
