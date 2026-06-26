from app.wh.runtime.vision.offer_verification_engine import (
    OfferVerificationEngine
)

from app.wh.runtime.vision.intelligent_vision_execution_result import (
    IntelligentVisionExecutionResult
)


def test_offer_verification_engine():

    engine = (

        OfferVerificationEngine()

    )

    execution_result = (

        IntelligentVisionExecutionResult(

            success=True,

            message="offer executed"

        )

    )

    result = (

        engine.verify(

            execution_result

        )

    )

    assert (

        result.success

        is True

    )

    assert (

        result.confidence

        ==

        0.99

    )