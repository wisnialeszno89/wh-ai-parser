from app.wh.runtime.vision.customer_prediction_engine import (
    CustomerPredictionEngine
)

from app.wh.runtime.vision.customer_preference import (
    CustomerPreference
)


def test_customer_prediction_engine():

    preference = (

        CustomerPreference(

            customer_name="Muller GmbH",

            profile_preference="Softline82",

            color_preference="Anthracite",

            addon_preference="RC2",

            confidence=0.91

        )

    )

    engine = (

        CustomerPredictionEngine()

    )

    prediction = (

        engine.predict(

            preference

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

        prediction.color

        ==

        "Anthracite"

    )

    assert (

        prediction.addon

        ==

        "RC2"

    )

    assert (

        prediction.confidence

        ==

        0.91

    )