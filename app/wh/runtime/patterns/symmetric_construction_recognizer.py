class SymmetricConstructionRecognizer:

    def matches(

        self,

        context

    ):

        return context.has(

            "balanced_grid"

        )

    def name(

        self

    ):

        return (

            "SYMMETRIC_CONSTRUCTION"

        )