from app.wh.runtime.vision.execution_record import (
    ExecutionRecord
)


def test_execution_record():

    record = (

        ExecutionRecord(

            goal="enable_rc2",

            success=True,

            reason="not_completed"

        )

    )

    assert (

        record.goal

        ==

        "enable_rc2"

    )

    assert (

        record.success

        is True

    )

    assert (

        record.reason

        ==

        "not_completed"

    )