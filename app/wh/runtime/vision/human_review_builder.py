from app.wh.runtime.vision.human_review_item import (
    HumanReviewItem
)

from app.wh.runtime.vision.human_review_package import (
    HumanReviewPackage
)


class HumanReviewBuilder:

    def build(

        self,

        brain

    ):

        package = (

            HumanReviewPackage()

        )

        summary = (

            brain.failure_analyzer.analyze(

                brain.failure_history

            )

        )

        if summary:

            package.top_failure_reason = (

                max(

                    summary,

                    key=summary.get

                )

            )

        for record in (

            brain.failure_history.records

        ):

            package.items.append(

                HumanReviewItem(

                    goal=record.goal,

                    reason=record.reason

                )

            )

        return package