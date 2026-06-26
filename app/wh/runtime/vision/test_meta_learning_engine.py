from app.wh.runtime.vision.meta_learning_engine import (
    MetaLearningEngine
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)

from app.wh.runtime.vision.alternative_strategy import (
    AlternativeStrategy
)


def test_meta_learning_engine():

    brain = (

        ProjectBrain()

    )

    engine = (

        MetaLearningEngine()

    )

    engine.learn(

        AlternativeStrategy.OCR_FALLBACK,

        brain

    )

    engine.learn(

        AlternativeStrategy.OCR_FALLBACK,

        brain

    )

    assert (

        brain.meta_learning_memory.count()

        ==

        1

    )

    assert (

        brain.meta_learning_memory.records[0].successes

        ==

        2

    )