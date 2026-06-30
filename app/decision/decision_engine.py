from app.context.offer_context import (
    OfferContext
)

from app.decision.decision_result import (
    DecisionResult
)


class DecisionEngine:

    def choose_workflow(
        self,
        context: OfferContext
    ) -> DecisionResult:

        if context.manual_review:

            return DecisionResult(
                workflow="manual_review",
                confidence=1.0,
                manual_review=True,
                reason="manual_review flag"
            )

        if (
            context.construction_type
            ==
            "single_window"
        ):

            return DecisionResult(
                workflow="single_window",
                confidence=1.0,
                manual_review=False,
                reason="construction_type=single_window"
            )

        return DecisionResult(
            workflow="manual_review",
            confidence=0.0,
            manual_review=True,
            reason="unknown construction"
        )