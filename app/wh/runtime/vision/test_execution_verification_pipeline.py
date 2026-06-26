from app.wh.runtime.vision.execution_verification_pipeline import (
    ExecutionVerificationPipeline
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)

from app.wh.runtime.vision.intelligent_vision_execution_result import (
    IntelligentVisionExecutionResult
)


def test_execution_verification_pipeline():

    brain = (

        ProjectBrain()

    )

    pipeline = (

        ExecutionVerificationPipeline(

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

        result.confidence

        ==

        0.99

    )