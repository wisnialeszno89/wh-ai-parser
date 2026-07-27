from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class Decision:
    """
    Decision returned by the Brain.

    It describes what Runtime should do next.
    """

    #
    # Action to execute.
    #

    action: Any | None = None

    #
    # Human readable reason.
    #

    reason: str = ""

    #
    # Skip current mission step.
    #

    skip: bool = False

    #
    # Retry last action.
    #

    retry: bool = False

    #
    # Confidence of the decision.
    #

    confidence: float = 1.0