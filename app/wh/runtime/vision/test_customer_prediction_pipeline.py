from app.wh.runtime.vision.customer_prediction_pipeline import (
    CustomerPredictionPipeline
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)


def test_customer_prediction_pipeline():

    brain = (

        ProjectBrain()

    )

    pipeline = (

        CustomerPredictionPipeline(

            brain

        )

    )

    result = (

        pipeline.execute(

            "Muller GmbH"

        )

    )

    assert (

        result.prediction.customer_name

        ==

        "Muller GmbH"

    )

    assert (

        result.prediction.profile

        ==

        "Softline82"

    )

    assert (

        result.prediction.color

        ==

        "Anthracite"

    )

    assert (

        result.prediction.addon

        ==

        "RC2"

    )