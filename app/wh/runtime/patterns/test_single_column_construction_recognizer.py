from app.wh.runtime.patterns.classification_context import (
    ClassificationContext
)

from app.wh.runtime.patterns.single_column_construction_recognizer import (
    SingleColumnConstructionRecognizer
)


def test_single_column_construction_recognizer():

    context = (

        ClassificationContext(

            [

                "single_column"

            ]

        )

    )

    recognizer = (

        SingleColumnConstructionRecognizer()

    )

    assert (

        recognizer.matches(

            context

        )

        is True

    )

    assert (

        recognizer.name()

        ==

        "SINGLE_COLUMN_CONSTRUCTION"

    )