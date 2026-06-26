from dataclasses import (
    dataclass
)


@dataclass
class HumanReviewItem:

    goal: str

    reason: str