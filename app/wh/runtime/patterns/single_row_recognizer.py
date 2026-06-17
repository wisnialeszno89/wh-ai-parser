class SingleRowRecognizer:

    def matches(

        self,

        signature

    ):

        return (

            signature.single_row

            and

            signature.columns > 1

        )