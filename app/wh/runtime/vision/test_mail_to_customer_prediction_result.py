from app.wh.runtime.vision.mail_to_customer_prediction_result import (
    MailToCustomerPredictionResult
)

from app.wh.runtime.vision.customer_prediction import (
    CustomerPrediction
)


def test_mail_to_customer_prediction_result():

    result = (

        MailToCustomerPredictionResult(

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