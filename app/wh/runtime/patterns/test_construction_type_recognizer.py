from app.wh.runtime.patterns.classification_context import (
    ClassificationContext
)

from app.wh.runtime.patterns.construction_type_recognizer import (
    ConstructionTypeRecognizer
)


def test_construction_type_recognizer():

    context = (

        ClassificationContext(

            [

                "balanced_grid"

            ]

        )

    )

    recognizer = (

        ConstructionTypeRecognizer()

    )

    result = (

        recognizer.recognize(

            context

        )

    )

    assert (

        "BALANCED_GRID_CONSTRUCTION"

        in result

    )