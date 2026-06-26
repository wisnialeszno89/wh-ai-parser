from app.wh.runtime.vision.offer_execution_plan import (
    OfferExecutionPlan
)


def test_offer_execution_plan():

    plan = (

        OfferExecutionPlan(

            customer_name="Muller GmbH",

            profile="Softline82",

            color="Anthracite",

            addon="RC2"

        )

    )

    assert (

        plan.customer_name

        ==

        "Muller GmbH"

    )

    assert (

        plan.profile

        ==

        "Softline82"

    )