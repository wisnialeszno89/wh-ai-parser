from app.wh.runtime.vision.recovery_learning_memory import (
    RecoveryLearningMemory
)

from app.wh.runtime.vision.alternative_strategy import (
    AlternativeStrategy
)


def test_recovery_learning_memory():

    memory = (

        RecoveryLearningMemory()

    )

    memory.remember(

        "template_not_found",

        AlternativeStrategy.OCR_FALLBACK

    )

    memory.remember(

        "template_not_found",

        AlternativeStrategy.OCR_FALLBACK

    )

    assert (

        memory.count()

        ==

        1

    )

    assert (

        memory.records[0].occurrences

        ==

        2

    )