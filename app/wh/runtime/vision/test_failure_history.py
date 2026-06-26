from app.wh.runtime.vision.failure_history import (
    FailureHistory
)

from app.wh.runtime.vision.failure_record import (
    FailureRecord
)


def test_failure_history():

    history = (

        FailureHistory()

    )

    history.remember(

        FailureRecord(

            goal="enable_rc2",

            reason="dialog_not_found"

        )

    )

    assert (

        history.count()

        ==

        1

    )