from app.wh.runtime.vision.offer_execution_plan import (
    OfferExecutionPlan
)


class OfferExecutionPlanner:

    def create_plan(

        self,

        offer

    ):

        return (

            OfferExecutionPlan(

                customer_name=(

                    offer.customer_name

                ),

                profile=(

                    offer.profile

                ),

                color=(

                    offer.color

                ),

                addon=(

                    offer.addon

                )

            )

        )