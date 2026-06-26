from app.wh.runtime.vision.customer_prediction_pipeline_result import (
    CustomerPredictionPipelineResult
)

from app.wh.runtime.vision.customer_prediction import (
    CustomerPrediction
)


def test_customer_prediction_pipeline_result():

    result = (

        CustomerPredictionPipelineResult(

            prediction=(

                CustomerPrediction(

                    customer_name="Muller GmbH",

                    profile="Softline82",

                    color="Anthracite",

                    addon="RC2",

                    confidence=0.91

                )

            )

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