class SingleColumnRecognizer:

    def matches(

        self,

        signature

    ):

        return (

            signature.single_column

            and

            signature.rows > 1

        )