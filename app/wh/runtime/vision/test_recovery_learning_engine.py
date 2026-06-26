from app.wh.runtime.vision.recovery_learning_engine import (
    RecoveryLearningEngine
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)

from app.wh.runtime.vision.alternative_strategy import (
    AlternativeStrategy
)


def test_recovery_learning_engine():

    brain = (

        ProjectBrain()

    )

    engine = (

        RecoveryLearningEngine()

    )

    engine.learn(

        "template_not_found",

        AlternativeStrategy.OCR_FALLBACK,

        brain

    )

    engine.learn(

        "template_not_found",

        AlternativeStrategy.OCR_FALLBACK,

        brain

    )

    assert (

        brain.recovery_learning_memory.count()

        ==

        1

    )

    assert (

        brain.recovery_learning_memory.records[0].occurrences

        ==

        2

    )