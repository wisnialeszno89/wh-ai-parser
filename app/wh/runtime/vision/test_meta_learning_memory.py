from app.wh.runtime.vision.meta_learning_memory import (
    MetaLearningMemory
)

from app.wh.runtime.vision.alternative_strategy import (
    AlternativeStrategy
)


def test_meta_learning_memory():

    memory = (

        MetaLearningMemory()

    )

    memory.remember(

        AlternativeStrategy.OCR_FALLBACK

    )

    memory.remember(

        AlternativeStrategy.OCR_FALLBACK

    )

    assert (

        memory.count()

        ==

        1

    )

    assert (

        memory.records[0].successes

        ==

        2

    )