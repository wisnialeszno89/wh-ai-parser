from app.wh.runtime.vision.self_healing_execution_pipeline import (
    SelfHealingExecutionPipeline
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)

from app.wh.runtime.vision.intelligent_vision_execution_result import (
    IntelligentVisionExecutionResult
)


def test_self_healing_execution_pipeline():

    brain = (

        ProjectBrain()

    )

    pipeline = (

        SelfHealingExecutionPipeline(

            brain

        )

    )

    execution_result = (

        IntelligentVisionExecutionResult(

            success=True,

            message="offer executed"

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