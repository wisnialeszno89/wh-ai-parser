from app.wh.runtime.vision.project_outcome import (
    ProjectOutcome
)


def test_project_outcome():

    outcome = (

        ProjectOutcome(

            project_name="Offer_001",

            success=True,

            execution_time_seconds=12.5,

            error_count=1

        )

    )

    assert (

        outcome.project_name

        ==

        "Offer_001"

    )

    assert (

        outcome.success

        is True

    )

    assert (

        outcome.execution_time_seconds

        ==

        12.5

    )

    assert (

        outcome.error_count

        ==

        1

    )