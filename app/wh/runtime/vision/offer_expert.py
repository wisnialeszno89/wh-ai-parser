from app.wh.runtime.vision.offer_specification import (
    OfferSpecification
)

from app.wh.runtime.vision.offer_requirements import (
    OfferRequirements
)

from app.wh.runtime.vision.products.window_product import (
    WindowProduct
)

from app.wh.runtime.vision.product_decision_engine import (
    ProductDecisionEngine
)


class OfferExpert:

    def __init__(

        self

    ):

        self.decision_engine = (

            ProductDecisionEngine()

        )

    def build_offer(

        self,

        requirements: OfferRequirements

    ) -> OfferSpecification:

        specification = (

            OfferSpecification(

                language=requirements.language

            )

        )

        profile = (

            self.decision_engine.choose_profile(

                requirements

            )

        )

        if requirements.windows > 0:

            specification.products.append(

                WindowProduct(

                    quantity=requirements.windows,

                    profile=profile or "",

                    outside_color=requirements.outside_color,

                    inside_color=requirements.inside_color,

                    glazing=requirements.glazing,

                    security=requirements.security

                )

            )

        return specification