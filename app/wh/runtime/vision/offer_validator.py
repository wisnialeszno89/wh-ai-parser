from app.wh.runtime.vision.offer_specification import (
    OfferSpecification
)


class OfferValidator:

    REQUIRED_FIELDS = (

        "profile",

        "outside_color",

        "inside_color",

        "glazing"

    )

    def validate(

        self,

        offer: OfferSpecification

    ):

        errors = []

        for index, product in enumerate(

            offer.products,

            start=1

        ):

            for field in self.REQUIRED_FIELDS:

                if not getattr(

                    product,

                    field

                ):

                    errors.append(

                        f"Product {index}: missing {field}"

                    )

        return errors