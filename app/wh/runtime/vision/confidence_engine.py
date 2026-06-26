from app.wh.runtime.vision.confidence_decision import (
    ConfidenceDecision
)

from app.wh.runtime.vision.confidence_level import (
    ConfidenceLevel
)


class ConfidenceEngine:

    def evaluate(

        self,

        confidence

    ):

        if (

            confidence

            >=

            100

        ):

            level = (

                ConfidenceLevel.VERY_HIGH

            )

        elif (

            confidence

            >=

            20

        ):

            level = (

                ConfidenceLevel.HIGH

            )

        elif (

            confidence

            >=

            5

        ):

            level = (

                ConfidenceLevel.MEDIUM

            )

        else:

            level = (

                ConfidenceLevel.LOW

            )

        return (

            ConfidenceDecision(

                level=level,

                confidence=confidence

            )

        )