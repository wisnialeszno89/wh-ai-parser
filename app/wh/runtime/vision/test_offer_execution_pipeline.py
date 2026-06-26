from app.wh.runtime.vision.offer_execution_pipeline import (
    OfferExecutionPipeline
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)

from app.wh.runtime.vision.offer_schema import (
    OfferSchema
)


def test_offer_execution_pipeline():

    brain = (

        ProjectBrain()

    )

    pipeline = (

        OfferExecutionPipeline(

            brain

        )

    )

    offer = (

        OfferSchema(

            customer_name="Muller GmbH",

            profile="Softline82",

            color="Anthracite",

            addon="RC2"

        )

    )

    result = (

        pipeline.execute(

            offer

        )

    )

    assert (

        result.execution_result.success

        is True

    )

    assert (

        result.execution_result.message

        ==

        "offer executed"

    )