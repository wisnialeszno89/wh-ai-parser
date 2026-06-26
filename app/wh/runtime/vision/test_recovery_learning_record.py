from app.wh.runtime.vision.recovery_learning_record import (
    RecoveryLearningRecord
)

from app.wh.runtime.vision.alternative_strategy import (
    AlternativeStrategy
)


def test_recovery_learning_record():

    record = (

        RecoveryLearningRecord(

            reason="template_not_found",

            strategy=(

                AlternativeStrategy.OCR_FALLBACK

            )

        )

    )

    assert (

        record.reason

        ==

        "template_not_found"

    )

    assert (

        record.strategy

        ==

        AlternativeStrategy.OCR_FALLBACK

    )

    assert (

        record.occurrences

        ==

        1

    )