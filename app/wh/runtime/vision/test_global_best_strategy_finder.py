from app.wh.runtime.vision.global_best_strategy_finder import (
    GlobalBestStrategyFinder
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)

from app.wh.runtime.vision.alternative_strategy import (
    AlternativeStrategy
)


def test_global_best_strategy_finder():

    brain = (

        ProjectBrain()

    )

    brain.meta_learning_memory.remember(

        AlternativeStrategy.OCR_FALLBACK

    )

    brain.meta_learning_memory.remember(

        AlternativeStrategy.OCR_FALLBACK

    )

    brain.meta_learning_memory.remember(

        AlternativeStrategy.CLICK_BY_COORDINATES

    )

    finder = (

        GlobalBestStrategyFinder()

    )

    result = (

        finder.find(

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