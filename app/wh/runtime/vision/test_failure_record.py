from app.wh.runtime.vision.failure_record import (
    FailureRecord
)


def test_failure_record():

    record = (

        FailureRecord(

            goal="enable_rc2",

            reason="dialog_not_found"

        )

    )

    assert (

        record.goal

        ==

        "enable_rc2"

    )

    assert (

        record.reason

        ==

        "dialog_not_found"

    )

    assert (

        record.recovery_attempts

        ==

        0

    )