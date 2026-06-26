from app.wh.runtime.vision.adaptive_recovery_engine import (
    AdaptiveRecoveryEngine
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)


def test_adaptive_recovery_engine():

    brain = (

        ProjectBrain()

    )

    brain.recovery_knowledge_base.remember(

        "OCR_ERROR",

        "OCR_FALLBACK",

        True

    )

    brain.recovery_knowledge_base.remember(

        "OCR_ERROR",

        "OCR_FALLBACK",

        True

    )

    engine = (

        AdaptiveRecoveryEngine()

    )

    result = (

        engine.recover(

            brain,

            "OCR_ERROR"

        )

    )

    assert (

        result.success

        is True

    )

    assert (

        result.strategy_used

        ==

        "OCR_FALLBACK"

    )

    assert (

        result.confidence

        ==

        1.0

    )