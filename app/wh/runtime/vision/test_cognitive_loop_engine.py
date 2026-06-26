from app.wh.runtime.vision.cognitive_loop_engine import (
    CognitiveLoopEngine
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)

from app.wh.runtime.vision.alternative_strategy import (
    AlternativeStrategy
)

from app.wh.runtime.vision.confidence_level import (
    ConfidenceLevel
)


def test_cognitive_loop_engine():

    brain = (

        ProjectBrain()

    )

    brain.meta_learning_memory.remember(

        AlternativeStrategy.OCR_FALLBACK

    )

    brain.meta_learning_memory.remember(

        AlternativeStrategy.OCR_FALLBACK

    )

    engine = (

        CognitiveLoopEngine()

    )

    report = (

        engine.run(

            brain

        )

    )

    assert (

        report.confidence_level

        ==

        ConfidenceLevel.LOW

    )

    assert (

        report.meta_patterns

        ==

        1

    )