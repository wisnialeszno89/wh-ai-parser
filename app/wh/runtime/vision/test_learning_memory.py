from app.wh.runtime.vision.learning_memory import (
    LearningMemory
)


def test_learning_memory():

    memory = (

        LearningMemory()

    )

    memory.remember(

        "database_error",

        "winchester"

    )

    memory.remember(

        "database_error",

        "winchester"

    )

    assert (

        memory.count()

        ==

        1

    )

    assert (

        memory.records[0].occurrences

        ==

        2

    )