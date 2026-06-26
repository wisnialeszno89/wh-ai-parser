from app.wh.runtime.vision.human_review_builder import (
    HumanReviewBuilder
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)

from app.wh.runtime.vision.failure_record import (
    FailureRecord
)


def test_human_review_builder():

    brain = (

        ProjectBrain()

    )

    brain.failure_history.remember(

        FailureRecord(

            goal="enable_contacts",

            reason="dialog_not_found"

        )

    )

    brain.failure_history.remember(

        FailureRecord(

            goal="set_winchester",

            reason="database_error"

        )

    )

    brain.failure_history.remember(

        FailureRecord(

            goal="enable_hidden_hinges",

            reason="database_error"

        )

    )

    builder = (

        HumanReviewBuilder()

    )

    package = (

        builder.build(

            brain

        )

    )

    assert (

        len(

            package.items

        )

        ==

        3

    )

    assert (

        package.top_failure_reason

        ==

        "database_error"

    )