class ConstructionReasoningEngine:

    def __init__(

        self,

        knowledge_context

    ):

        self.context = (

            knowledge_context

        )

    def is_single_row(

        self

    ):

        return self.context.has(

            "SINGLE_ROW_CONSTRUCTION"

        )

    def is_single_column(

        self

    ):

        return self.context.has(

            "SINGLE_COLUMN_CONSTRUCTION"

        )

    def is_balanced(

        self

    ):

        return self.context.has(

            "BALANCED_GRID_CONSTRUCTION"

        )

    def is_symmetric(

        self

    ):

        return self.context.has(

            "SYMMETRIC_CONSTRUCTION"

        )