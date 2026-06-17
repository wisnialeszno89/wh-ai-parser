class PSKRecognizer:

    def matches(

        self,

        reasoning

    ):

        return (

            reasoning.is_single_row()

            and

            not reasoning.is_symmetric()

        )

    def name(

        self

    ):

        return "PSK"