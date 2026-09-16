from app.knowledge.openings.opening_repository import (
    OpeningRepository
)

from app.knowledge.constructions.construction_repository import (
    ConstructionRepository
)


class ConstructionResolver:

    def __init__(
        self,
        opening_repository=None,
        construction_repository=None
    ):

        self.opening_repository = (
            opening_repository
            or OpeningRepository()
        )

        self.construction_repository = (
            construction_repository
            or ConstructionRepository()
        )

    def resolve(self, openings):

        resolved_fields = []

        for opening in openings:

            definition = (
                self.opening_repository
                .get_by_code_or_alias(opening)
            )

            if definition is None:
                return None

            resolved_fields.append(definition.code)

        return self.construction_repository.get_by_fields(
            resolved_fields
        )
