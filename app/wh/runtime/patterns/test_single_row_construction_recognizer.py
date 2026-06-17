from app.wh.runtime.patterns.classification_context import (
    ClassificationContext
)

from app.wh.runtime.patterns.single_row_construction_recognizer import (
    SingleRowConstructionRecognizer
)


def test_single_row_construction_recognizer():

    context = (

        ClassificationContext(

            [

                "single_row"

            ]

        )

    )

    recognizer = (

        SingleRowConstructionRecognizer()

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

        "SINGLE_ROW_CONSTRUCTION"

    )