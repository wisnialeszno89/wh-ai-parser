class BalancedGridRecognizer:

    def matches(

        self,

        signature

    ):

        return (

            signature.balanced

            and

            signature.rows > 1

            and

            signature.columns > 1

        )