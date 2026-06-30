from app.context.offer_context import (
    OfferContext
)

from app.decision.decision_engine import (
    DecisionEngine
)


def test_single_window():

    context = OfferContext()

    context.construction_type = (
        "single_window"
    )

    result = (
        DecisionEngine()
        .choose_workflow(
            context
        )
    )

    assert result.workflow == "single_window"

    assert result.manual_review is False

    assert result.confidence == 1.0