class SingleColumnConstructionRecognizer:

    def matches(

        self,

        context

    ):

        return context.has(

            "single_column"

        )

    def name(

        self

    ):

        return (

            "SINGLE_COLUMN_CONSTRUCTION"

        )