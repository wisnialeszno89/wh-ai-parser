from app.wh.runtime.construction_offer import (
    ConstructionOffer
)

from app.wh.runtime.color_parser import (
    ColorParser
)

from app.wh.runtime.profile_parser import (
    ProfileParser
)

from app.wh.runtime.glass_parser import (
    GlassParser
)

from app.wh.runtime.security_parser import (
    SecurityParser
)

from app.wh.runtime.hardware_parser import (
    HardwareParser
)

from app.wh.runtime.accessory_parser import (
    AccessoryParser
)


class OfferEnricher:

    def __init__(

        self

    ):

        self.color_parser = (

            ColorParser()

        )

        self.profile_parser = (

            ProfileParser()

        )

        self.glass_parser = (

            GlassParser()

        )

        self.security_parser = (

            SecurityParser()

        )

        self.hardware_parser = (

            HardwareParser()

        )

        self.accessory_parser = (

            AccessoryParser()

        )

    def enrich(

        self,

        text

    ):

        offer = (

            ConstructionOffer()

        )

        (

            offer.color_inside,

            offer.color_outside

        ) = (

            self.color_parser.parse(

                text

            )

        )

        offer.profile = (

            self.profile_parser.parse(

                text

            )

        )

        offer.glass = (

            self.glass_parser.parse(

                text

            )

        )

        offer.security = (

            self.security_parser.parse(

                text

            )

        )

        offer.hardware = (

            self.hardware_parser.parse(

                text

            )

        )

        offer.accessories = (

            self.accessory_parser.parse(

                text

            )

        )

        return offer