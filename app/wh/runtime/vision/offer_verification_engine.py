from app.wh.runtime.vision.offer_verification_result import (
    OfferVerificationResult
)


class OfferVerificationEngine:

    def verify(

        self,

        execution_result

    ):

        if (

            execution_result.success

        ):

            return (

                OfferVerificationResult(

                    success=True,

                    confidence=0.99,

                    message="verified"

                )

            )

        return (

            OfferVerificationResult(

                success=False,

                confidence=0.0,

                message="verification failed"

            )

        )