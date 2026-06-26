from app.wh.runtime.vision.adaptive_self_healing_pipeline import (
    AdaptiveSelfHealingPipeline
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)

from app.wh.runtime.vision.intelligent_vision_execution_result import (
    IntelligentVisionExecutionResult
)


def test_adaptive_self_healing_pipeline():

    brain = (

        ProjectBrain()

    )

    brain.recovery_knowledge_base.remember(

        "OCR_ERROR",

        "OCR_FALLBACK",

        True

    )

    execution_result = (

        IntelligentVisionExecutionResult(

            success=True,

            message="offer executed"

        )

    )

    pipeline = (

        AdaptiveSelfHealingPipeline(

            brain

        )

    )

    result = (

        pipeline.execute(

            execution_result

        )

    )

    assert (

        result.success

        is True

    )

    assert (

        result.retries_used

        ==

        0

    )

    assert (

        result.confidence

        ==

        0.99

    )