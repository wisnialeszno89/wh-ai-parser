from app.wh.runtime.vision.project_execution_history import (
    ProjectExecutionHistory
)

from app.wh.runtime.vision.project_outcome import (
    ProjectOutcome
)


def test_project_execution_history():

    history = (

        ProjectExecutionHistory()

    )

    history.remember(

        ProjectOutcome(

            project_name="Offer_001",

            success=True

        )

    )

    history.remember(

        ProjectOutcome(

            project_name="Offer_002",

            success=False

        )

    )

    assert (

        history.count()

        ==

        2

    )

    assert (

        history.last().project_name

        ==

        "Offer_002"

    )