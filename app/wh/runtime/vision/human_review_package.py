from dataclasses import (
    dataclass,
    field
)

from app.wh.runtime.vision.human_review_item import (
    HumanReviewItem
)


@dataclass
class HumanReviewPackage:

    items: list[HumanReviewItem] = field(

        default_factory=list

    )

    top_failure_reason: str | None = None