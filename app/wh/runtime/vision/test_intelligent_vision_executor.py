from app.wh.runtime.vision.intelligent_vision_executor import (
    IntelligentVisionExecutor
)

from app.wh.runtime.vision.offer_execution_plan import (
    OfferExecutionPlan
)


def test_intelligent_vision_executor():

    plan = (

        OfferExecutionPlan(

            customer_name="Muller GmbH",

            profile="Softline82",

            color="Anthracite",

            addon="RC2"

        )

    )

    executor = (

        IntelligentVisionExecutor()

    )

    result = (

        executor.execute(

            plan

        )

    )

    assert (

        result.success

        is True

    )

    assert (

        result.message

        ==

        "offer executed"

    )