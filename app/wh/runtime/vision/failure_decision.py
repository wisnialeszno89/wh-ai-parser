from dataclasses import (
    dataclass
)

from app.wh.runtime.vision.failure_action import (
    FailureAction
)


@dataclass
class FailureDecision:

    action: FailureAction

    reason: str