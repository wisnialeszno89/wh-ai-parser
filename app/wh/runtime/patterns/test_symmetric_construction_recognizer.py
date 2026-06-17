from app.wh.runtime.patterns.classification_context import (
    ClassificationContext
)

from app.wh.runtime.patterns.symmetric_construction_recognizer import (
    SymmetricConstructionRecognizer
)


def test_symmetric_construction_recognizer():

    context = (

        ClassificationContext(

            [

                "balanced_grid"

            ]

        )

    )

    recognizer = (

        SymmetricConstructionRecognizer()

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

        "SYMMETRIC_CONSTRUCTION"

    )