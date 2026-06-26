from app.wh.runtime.vision.global_recovery_optimizer import (
    GlobalRecoveryOptimizer
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)

from app.wh.runtime.vision.alternative_strategy import (
    AlternativeStrategy
)


def test_global_recovery_optimizer():

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

    optimizer = (

        GlobalRecoveryOptimizer()

    )

    decision = (

        optimizer.optimize(

            "template_not_found",

            brain

        )

    )

    assert (

        decision is not None

    )

    assert (

        decision.strategy

        ==

        AlternativeStrategy.OCR_FALLBACK

    )

    assert (

        decision.confidence

        ==

        2

    )