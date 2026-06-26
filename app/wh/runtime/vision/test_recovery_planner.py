from app.wh.runtime.vision.recovery_planner import (
    RecoveryPlanner
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)

from app.wh.runtime.vision.alternative_strategy import (
    AlternativeStrategy
)


def test_recovery_planner():

    planner = (

        RecoveryPlanner()

    )

    brain = (

        ProjectBrain()

    )

    plan = (

        planner.create(

            "template_not_found",

            brain

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