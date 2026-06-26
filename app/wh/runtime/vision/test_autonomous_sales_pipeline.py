from app.wh.runtime.vision.autonomous_sales_pipeline import (
    AutonomousSalesPipeline
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)


def test_autonomous_sales_pipeline():

    brain = (

        ProjectBrain()

    )

    pipeline = (

        AutonomousSalesPipeline(

            brain

        )

    )

    result = (

        pipeline.execute(

            "Please prepare quotation"

        )

    )

    assert (

        result.success

        is True

    )

    assert (

        result.message

        ==

        "pipeline completed"

    )