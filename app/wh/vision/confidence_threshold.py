class ConfidenceThreshold:

    def __init__(

        self,

        threshold=0.9

    ):

        self.threshold = threshold

    def validate(

        self,

        result

    ):

        if (

            result.confidence

            <

            self.threshold

        ):

            raise ValueError(

                f"Low confidence: "

                f"{result.confidence}"

            )

        return result