from app.wh.runtime.vision.self_optimization_engine import (
    SelfOptimizationEngine
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


def test_self_optimization_engine():

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

        SelfOptimizationEngine()

    )

    report = (

        engine.analyze(

            brain

        )

    )

    assert (

        report.confidence_level

        ==

        ConfidenceLevel.LOW

    )

    assert (

        report.total_meta_patterns

        ==

        1

    )