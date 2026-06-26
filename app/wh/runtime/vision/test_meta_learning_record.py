from app.wh.runtime.vision.meta_learning_record import (
    MetaLearningRecord
)

from app.wh.runtime.vision.alternative_strategy import (
    AlternativeStrategy
)


def test_meta_learning_record():

    record = (

        MetaLearningRecord(

            strategy=(

                AlternativeStrategy.OCR_FALLBACK

            ),

            successes=5

        )

    )

    assert (

        record.strategy

        ==

        AlternativeStrategy.OCR_FALLBACK

    )

    assert (

        record.successes

        ==

        5

    )