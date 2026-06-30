from app.context.offer_context import (
    OfferContext
)

from app.construction.models.construction import (
    Construction
)

from app.construction.models.field import (
    Field
)

from app.construction.models.opening import (
    Opening
)

from app.construction.models.opening_type import (
    OpeningType
)

from app.construction.models.opening_direction import (
    OpeningDirection
)

from app.knowledge.openings.opening_repository import (
    OpeningRepository
)

from app.knowledge.constructions.construction_repository import (
    ConstructionRepository
)


class ConstructionBuilder:

    def __init__(self):

        self.opening_repository = OpeningRepository()

        self.construction_repository = (
            ConstructionRepository()
        )

    def build(
        self,
        context: OfferContext
    ) -> Construction:

        construction = Construction(

            width=context.width,

            height=context.height
        )

        definition = (

            self.construction_repository.get_by_code(
                context.construction_type
            )
        )

        if definition is None:

            return construction

        for field_code in definition.fields:

            opening_definition = (

                self.opening_repository.get_by_code(
                    field_code
                )
            )

            if opening_definition is None:

                continue

            opening = Opening(

                type=OpeningType[
                    opening_definition.opening_type
                ],

                direction=OpeningDirection[
                    opening_definition.direction
                ]
            )

            construction.add_field(

                Field(

                    opening=opening,

                    width=context.width,

                    height=context.height,

                    color=context.color,

                    # Tymczasowo na sztywno.
                    # Za chwilę będą pobierane z Knowledge.
                    frame="VEKA82_MD",

                    glass="PERFECT_48",

                    hardware="WINKHAUS_PRO",

                    extension=None
                )
            )

        return construction