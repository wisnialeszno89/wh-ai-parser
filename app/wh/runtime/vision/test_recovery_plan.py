from app.wh.runtime.vision.recovery_plan import (
    RecoveryPlan
)

from app.wh.runtime.vision.alternative_strategy import (
    AlternativeStrategy
)


def test_recovery_plan():

    plan = (

        RecoveryPlan(

            strategy=(

                AlternativeStrategy.OCR_FALLBACK

            ),

            reason="template_not_found"

        )

    )

    assert (

        plan.strategy

        ==

        AlternativeStrategy.OCR_FALLBACK

    )

    assert (

        plan.reason

        ==

        "template_not_found"

    )