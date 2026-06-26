from app.wh.runtime.vision.offer_verification_result import (
    OfferVerificationResult
)


def test_offer_verification_result():

    result = (

        OfferVerificationResult(

            success=True,

            confidence=0.98,

            message="verified"

        )

    )

    assert (

        result.success

        is True

    )

    assert (

        result.confidence

        ==

        0.98

    )