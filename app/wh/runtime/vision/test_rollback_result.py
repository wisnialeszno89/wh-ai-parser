from app.wh.runtime.vision.rollback_result import (
    RollbackResult
)


def test_rollback_result():

    result = (

        RollbackResult(

            success=True

        )

    )

    assert (

        result.success

        is True

    )

    assert (

        result.restored_snapshot

        is None

    )