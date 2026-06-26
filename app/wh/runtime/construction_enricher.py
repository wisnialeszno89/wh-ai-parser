from app.wh.runtime.construction_offer import (
    ConstructionOffer
)


class ConstructionEnricher:

    def enrich(

        self,

        features

    ):

        offer = (

            ConstructionOffer()

        )

        offer.color_inside = (

            features.color_inside

        )

        offer.color_outside = (

            features.color_outside

        )

        offer.glass.type = (

            features.glass

        )

        offer.glass.thickness_mm = (

            features.glass_package_mm

        )

        offer.glass.warm_edge = (

            features.warm_edge

        )

        offer.glass.swisspacer = (

            features.swisspacer

        )

        offer.glass.security_p4 = (

            features.security_glass_p4

        )

        offer.security.rc2 = (

            features.security_class_rc2

        )

        offer.security.contacts = (

            features.contacts

        )

        offer.hardware.hidden_hinges = (

            features.hidden_hinges

        )

        offer.hardware.v_perfect = (

            features.v_perfect

        )

        return offer