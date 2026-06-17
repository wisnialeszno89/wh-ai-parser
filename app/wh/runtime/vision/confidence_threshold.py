class ConfidenceThreshold:

    def __init__(

        self,

        threshold=0.9

    ):

        self.threshold = (

            threshold

        )

    def accepts(

        self,

        confidence

    ):

        return (

            confidence >=

            self.threshold

        )