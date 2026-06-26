from app.wh.runtime.vision.learning_record import (
    LearningRecord
)


def test_learning_record():

    record = (

        LearningRecord(

            key="database_error",

            value="winchester"

        )

    )

    assert (

        record.key

        ==

        "database_error"

    )

    assert (

        record.value

        ==

        "winchester"

    )

    assert (

        record.occurrences

        ==

        1

    )