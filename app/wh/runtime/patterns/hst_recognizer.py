class HSTRecognizer:

    def matches(

        self,

        reasoning

    ):

        return (

            reasoning.is_single_row()

            and

            reasoning.is_symmetric()

        )

    def name(

        self

    ):

        return "HST"