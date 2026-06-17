from app.wh.vision.confidence_threshold import (
    ConfidenceThreshold
)


class MatchValidator:

    def is_valid(

        self,

        result

    ):

        return (

            result.confidence

            >=

            ConfidenceThreshold.DEFAULT

        )