from app.wh.runtime.vision.failure_pipeline import (
    FailurePipeline
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)


def test_failure_pipeline():

    brain = (

        ProjectBrain()

    )

    brain.gui_state.current_dialog = (

        "glass"

    )

    pipeline = (

        FailurePipeline()

    )

    result = (

        pipeline.handle(

            "dialog_not_found",

            brain

        )

    )

    assert (

        result

        is True

    )

    assert (

        brain.gui_state.current_dialog

        is None

    )