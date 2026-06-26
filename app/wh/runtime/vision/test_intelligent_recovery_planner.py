from app.wh.runtime.vision.intelligent_recovery_planner import (
    IntelligentRecoveryPlanner
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)

from app.wh.runtime.vision.alternative_strategy import (
    AlternativeStrategy
)


def test_intelligent_recovery_planner():

    brain = (

        ProjectBrain()

    )

    brain.recovery_learning_memory.remember(

        "template_not_found",

        AlternativeStrategy.OCR_FALLBACK

    )

    brain.recovery_learning_memory.remember(

        "template_not_found",

        AlternativeStrategy.OCR_FALLBACK

    )

    planner = (

        IntelligentRecoveryPlanner()

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