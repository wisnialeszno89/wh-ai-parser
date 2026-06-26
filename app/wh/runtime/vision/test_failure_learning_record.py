from app.wh.runtime.vision.failure_learning_record import (
    FailureLearningRecord
)


def test_failure_learning_record():

    record = (

        FailureLearningRecord(

            failure_reason="OCR_ERROR",

            recovery_strategy="OCR_FALLBACK",

            successful=True

        )

    )

    assert (

        record.failure_reason

        ==

        "OCR_ERROR"

    )

    assert (

        record.recovery_strategy

        ==

        "OCR_FALLBACK"

    )

    assert (

        record.successful

        is True

    )