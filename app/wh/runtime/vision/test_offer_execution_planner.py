from app.wh.runtime.vision.offer_execution_planner import (
    OfferExecutionPlanner
)

from app.wh.runtime.vision.offer_schema import (
    OfferSchema
)


def test_offer_execution_planner():

    offer = (

        OfferSchema(

            customer_name="Muller GmbH",

            profile="Softline82",

            color="Anthracite",

            addon="RC2"

        )

    )

    planner = (

        OfferExecutionPlanner()

    )

    plan = (

        planner.create_plan(

            offer

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

    assert (

        plan.color

        ==

        "Anthracite"

    )

    assert (

        plan.addon

        ==

        "RC2"

    )