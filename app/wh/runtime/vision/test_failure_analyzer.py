from app.wh.runtime.vision.failure_analyzer import (
    FailureAnalyzer
)

from app.wh.runtime.vision.failure_history import (
    FailureHistory
)

from app.wh.runtime.vision.failure_record import (
    FailureRecord
)


def test_failure_analyzer():

    history = (

        FailureHistory()

    )

    history.remember(

        FailureRecord(

            goal="enable_rc2",

            reason="dialog_not_found"

        )

    )

    history.remember(

        FailureRecord(

            goal="enable_contacts",

            reason="dialog_not_found"

        )

    )

    history.remember(

        FailureRecord(

            goal="enable_hidden_hinges",

            reason="database_error"

        )

    )

    analyzer = (

        FailureAnalyzer()

    )

    summary = (

        analyzer.analyze(

            history

        )

    )

    assert (

        summary[

            "dialog_not_found"

        ]

        ==

        2

    )

    assert (

        summary[

            "database_error"

        ]

        ==

        1

    )