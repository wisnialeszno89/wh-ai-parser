class ConstructionMemory:

    def __init__(self):

        self.constructions = {}

    def add(
        self,
        construction
    ):

        self.constructions[
            construction.id
        ] = construction

    def get(
        self,
        construction_id
    ):

        return self.constructions.get(
            construction_id
        )