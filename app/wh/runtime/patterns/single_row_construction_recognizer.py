class SingleRowConstructionRecognizer:

    def matches(

        self,

        context

    ):

        return context.has(

            "single_row"

        )

    def name(

        self

    ):

        return (

            "SINGLE_ROW_CONSTRUCTION"

        )