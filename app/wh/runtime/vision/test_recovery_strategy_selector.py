from app.wh.runtime.vision.recovery_strategy_selector import (
    RecoveryStrategySelector
)

from app.wh.runtime.vision.recovery_knowledge_base import (
    RecoveryKnowledgeBase
)


def test_recovery_strategy_selector():

    kb = (

        RecoveryKnowledgeBase()

    )

    kb.remember(

        "OCR_ERROR",

        "OCR_FALLBACK",

        True

    )

    kb.remember(

        "OCR_ERROR",

        "OCR_FALLBACK",

        True

    )

    kb.remember(

        "OCR_ERROR",

        "FULL_RETRY",

        False

    )

    selector = (

        RecoveryStrategySelector()

    )

    recommendation = (

        selector.recommend(

            kb,

            "OCR_ERROR"

        )

    )

    assert (

        recommendation.recovery_strategy

        ==

        "OCR_FALLBACK"

    )

    assert (

        recommendation.confidence

        ==

        1.0

    )