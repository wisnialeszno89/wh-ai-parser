from app.wh.runtime.vision.best_recovery_strategy_finder import (
    BestRecoveryStrategyFinder
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)

from app.wh.runtime.vision.alternative_strategy import (
    AlternativeStrategy
)


def test_best_recovery_strategy_finder():

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

    brain.recovery_learning_memory.remember(

        "template_not_found",

        AlternativeStrategy.CLICK_BY_COORDINATES

    )

    finder = (

        BestRecoveryStrategyFinder()

    )

    result = (

        finder.find(

            "template_not_found",

            brain

        )

    )

    assert (

        result

        is not None

    )

    assert (

        result.strategy

        ==

        AlternativeStrategy.OCR_FALLBACK

    )

    assert (

        result.confidence

        ==

        2

    )