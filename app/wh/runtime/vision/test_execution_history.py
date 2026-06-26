from app.wh.runtime.vision.execution_history import (
    ExecutionHistory
)

from app.wh.runtime.vision.execution_record import (
    ExecutionRecord
)


def test_execution_history():

    history = (

        ExecutionHistory()

    )

    history.remember(

        ExecutionRecord(

            goal="enable_rc2",

            success=True,

            reason="not_completed"

        )

    )

    assert (

        history.count()

        ==

        1

    )