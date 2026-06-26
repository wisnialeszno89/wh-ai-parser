from app.wh.runtime.vision.offer_schema import (
    OfferSchema
)


class OfferBuilder:

    def build(

        self,

        prediction

    ):

        return (

            OfferSchema(

                customer_name=(

                    prediction.customer_name

                ),

                profile=(

                    prediction.profile

                ),

                color=(

                    prediction.color

                ),

                addon=(

                    prediction.addon

                )

            )

        )