from app.context.offer_context import (
    OfferContext
)

from app.catalog.profiles import (
    DEFAULT_PROFILE,
    PROFILE_CATALOG,
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

        print()
        print("========== BUILDER ==========")
        print("Requested:", context.construction_type)

        definition = self.construction_repository.get_by_code(
            context.construction_type
        )

        print("Definition:", definition)
        print("=============================")

        if definition is None:

            return construction

        if context.manual_review:

            return construction

        profile_code = (
            context.profile
            if context.profile is not None
            else DEFAULT_PROFILE
        )

        profile = PROFILE_CATALOG.get(
            profile_code
        )

        if profile is None:

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

                    frame=profile.default_frame,

                    glass=profile.default_glass,

                    hardware=profile.default_hardware,

                    extension=None
                )
            )

        return construction
