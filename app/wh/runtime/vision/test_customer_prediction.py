from app.wh.runtime.vision.customer_prediction import (
    CustomerPrediction
)


def test_customer_prediction():

    prediction = (

        CustomerPrediction(

            customer_name="Muller GmbH",

            profile="Softline82",

            color="Anthracite",

            addon="RC2",

            confidence=0.91

        )

    )

    assert (

        prediction.customer_name

        ==

        "Muller GmbH"

    )

    assert (

        prediction.profile

        ==

        "Softline82"

    )

    assert (

        prediction.confidence

        ==

        0.91

    )