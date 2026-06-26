from app.wh.runtime.vision.customer_recognition_result import (
    CustomerRecognitionResult
)


def test_customer_recognition_result():

    result = (

        CustomerRecognitionResult(

            customer_name="Muller GmbH",

            recognized=True

        )

    )

    assert (

        result.customer_name

        ==

        "Muller GmbH"

    )

    assert (

        result.recognized

        is True

    )