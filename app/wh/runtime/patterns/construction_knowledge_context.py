class ConstructionKnowledgeContext:

    def __init__(

        self,

        types

    ):

        self.types = types

    def has(

        self,

        construction_type

    ):

        return (

            construction_type

            in

            self.types

        )

    def has_any(

        self,

        *types

    ):

        return any(

            t in self.types

            for t in types

        )

    def has_all(

        self,

        *types

    ):

        return all(

            t in self.types

            for t in types

        )